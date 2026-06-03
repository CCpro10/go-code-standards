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
	includeTests := flag.Bool("include-tests", false, "include _test.go files in declaration order checks")
	flag.Parse()

	root, err := filepath.Abs(*repo)
	if err != nil {
		fail("resolve repo: %v", err)
	}

	pkgs := map[packageKey][]declaration{}
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

		file, err := parser.ParseFile(fset, path, src, parser.SkipObjectResolution)
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

	var violations []string
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

	fmt.Println("[ok] package declaration order")
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
