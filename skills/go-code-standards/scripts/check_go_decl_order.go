package main

import (
	"bytes"
	"flag"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"unicode"
)

var generatedRE = regexp.MustCompile(`(?m)^// Code generated .* DO NOT EDIT\.$`)

type declaration struct {
	name     string
	file     string
	line     int
	exported bool
}

type packageKey struct {
	dir  string
	name string
}

func main() {
	repo := flag.String("repo", ".", "repository root")
	includeTests := flag.Bool("include-tests", false, "include _test.go files in declaration style checks")
	flag.Parse()

	root, err := filepath.Abs(*repo)
	if err != nil {
		fail("resolve repo: %v", err)
	}

	pkgs := map[packageKey][]declaration{}
	var violations []string
	fset := token.NewFileSet()
	err = filepath.WalkDir(root, func(path string, entry os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if entry.IsDir() {
			if path != root && shouldSkipDir(entry.Name()) {
				return filepath.SkipDir
			}
			return nil
		}
		if !strings.HasSuffix(entry.Name(), ".go") {
			return nil
		}
		if !*includeTests && strings.HasSuffix(entry.Name(), "_test.go") {
			return nil
		}

		src, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		if isGenerated(src) {
			return nil
		}

		file, err := parser.ParseFile(fset, path, src, parser.ParseComments|parser.SkipObjectResolution)
		if err != nil {
			return fmt.Errorf("%s: %w", path, err)
		}

		rel, err := filepath.Rel(root, path)
		if err != nil {
			return err
		}
		dir, err := filepath.Rel(root, filepath.Dir(path))
		if err != nil {
			return err
		}
		key := packageKey{dir: filepath.ToSlash(dir), name: file.Name.Name}

		violations = append(violations, checkStructComments(fset, filepath.ToSlash(rel), file)...)

		for _, decl := range file.Decls {
			fn, ok := decl.(*ast.FuncDecl)
			if !ok || fn.Name == nil || fn.Name.Name == "init" {
				continue
			}
			pos := fset.Position(fn.Pos())
			pkgs[key] = append(pkgs[key], declaration{
				name:     fn.Name.Name,
				file:     filepath.ToSlash(rel),
				line:     pos.Line,
				exported: startsWithUpper(fn.Name.Name),
			})
		}
		return nil
	})
	if err != nil {
		fail("%v", err)
	}

	for key, decls := range pkgs {
		sort.Slice(decls, func(i, j int) bool {
			if decls[i].file != decls[j].file {
				return decls[i].file < decls[j].file
			}
			return decls[i].line < decls[j].line
		})

		var firstPrivate *declaration
		for i := range decls {
			decl := decls[i]
			if !decl.exported {
				if firstPrivate == nil {
					copyDecl := decl
					firstPrivate = &copyDecl
				}
				continue
			}
			if firstPrivate != nil {
				violations = append(violations, fmt.Sprintf(
					"%s:%d: %s is uppercase/exported but appears after private section started at %s:%d in package %s",
					decl.file,
					decl.line,
					decl.name,
					firstPrivate.file,
					firstPrivate.line,
					formatPackage(key),
				))
			}
		}
	}

	if len(violations) > 0 {
		for _, violation := range violations {
			fmt.Fprintln(os.Stderr, violation)
		}
		os.Exit(1)
	}

	fmt.Println("[ok] Go declaration style")
}

func checkStructComments(fset *token.FileSet, rel string, file *ast.File) []string {
	var violations []string
	for _, decl := range file.Decls {
		gen, ok := decl.(*ast.GenDecl)
		if !ok || gen.Tok != token.TYPE {
			continue
		}
		for _, spec := range gen.Specs {
			typeSpec, ok := spec.(*ast.TypeSpec)
			if !ok || typeSpec.Name == nil {
				continue
			}
			structType, ok := typeSpec.Type.(*ast.StructType)
			if !ok || !startsWithUpper(typeSpec.Name.Name) {
				continue
			}

			docGroups := []*ast.CommentGroup{typeSpec.Doc}
			if len(gen.Specs) == 1 {
				docGroups = append(docGroups, gen.Doc)
			}
			if !hasDetailedComment(typeSpec.Name.Name, docGroups...) {
				pos := fset.Position(typeSpec.Pos())
				violations = append(violations, fmt.Sprintf(
					"%s:%d: exported struct %s must have a detailed comment that explains its meaning or boundary",
					rel,
					pos.Line,
					typeSpec.Name.Name,
				))
			}

			for _, field := range structType.Fields.List {
				violations = append(violations, checkExportedStructFieldComments(fset, rel, typeSpec.Name.Name, field)...)
			}
		}
	}
	return violations
}

func checkExportedStructFieldComments(fset *token.FileSet, rel, structName string, field *ast.Field) []string {
	var violations []string
	if len(field.Names) == 0 {
		fieldName := embeddedFieldName(field.Type)
		if fieldName == "" {
			fieldName = "embedded field"
		}
		if !hasClearComment(fieldName, field.Doc, field.Comment) {
			pos := fset.Position(field.Pos())
			violations = append(violations, fmt.Sprintf(
				"%s:%d: field %s.%s in exported struct must have a clear comment",
				rel,
				pos.Line,
				structName,
				fieldName,
			))
		}
		return violations
	}

	for _, name := range field.Names {
		if name.Name == "_" {
			continue
		}
		if !hasClearComment(name.Name, field.Doc, field.Comment) {
			pos := fset.Position(name.Pos())
			violations = append(violations, fmt.Sprintf(
				"%s:%d: field %s.%s in exported struct must have a clear comment",
				rel,
				pos.Line,
				structName,
				name.Name,
			))
		}
	}
	return violations
}

func hasDetailedComment(name string, groups ...*ast.CommentGroup) bool {
	text := commentText(groups...)
	if len(text) < 30 {
		return false
	}
	return containsWord(text, name)
}

func hasClearComment(name string, groups ...*ast.CommentGroup) bool {
	text := commentText(groups...)
	if len(text) < 8 {
		return false
	}
	return strings.Contains(strings.ToLower(text), strings.ToLower(name)) || len(strings.Fields(text)) >= 3
}

func commentText(groups ...*ast.CommentGroup) string {
	var parts []string
	for _, group := range groups {
		if group == nil {
			continue
		}
		if text := strings.TrimSpace(group.Text()); text != "" {
			parts = append(parts, text)
		}
	}
	return strings.Join(parts, "\n")
}

func containsWord(text, word string) bool {
	for _, field := range strings.FieldsFunc(text, func(r rune) bool {
		return !unicode.IsLetter(r) && !unicode.IsDigit(r) && r != '_'
	}) {
		if field == word {
			return true
		}
	}
	return false
}

func embeddedFieldName(expr ast.Expr) string {
	switch value := expr.(type) {
	case *ast.Ident:
		return value.Name
	case *ast.SelectorExpr:
		return value.Sel.Name
	case *ast.StarExpr:
		return embeddedFieldName(value.X)
	default:
		return ""
	}
}

func shouldSkipDir(name string) bool {
	switch name {
	case ".git", ".hg", ".svn", ".idea", ".vscode", "node_modules", "vendor", "third_party":
		return true
	default:
		return false
	}
}

func isGenerated(src []byte) bool {
	head := src
	if len(head) > 4096 {
		head = head[:4096]
	}
	return generatedRE.Match(head) || bytes.Contains(head, []byte("DO NOT EDIT"))
}

func startsWithUpper(name string) bool {
	for _, r := range name {
		return unicode.IsUpper(r)
	}
	return false
}

func formatPackage(key packageKey) string {
	if key.dir == "." {
		return key.name
	}
	return key.dir + " (" + key.name + ")"
}

func fail(format string, args ...any) {
	fmt.Fprintf(os.Stderr, format+"\n", args...)
	os.Exit(2)
}
