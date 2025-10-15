package tui

import (
	"github.com/charmbracelet/glamour"
	"github.com/charmbracelet/glamour/ansi"
	"github.com/charmbracelet/glamour/styles"
	"github.com/charmbracelet/lipgloss"
	"github.com/charmbracelet/lipgloss/v2/compat"
	"github.com/lucasb-eyer/go-colorful"
	"github.com/rogue/tui/internal/theme"
)

const defaultMargin = 1

// Helper functions for style pointers
func boolPtr(b bool) *bool       { return &b }
func stringPtr(s string) *string { return &s }
func uintPtr(u uint) *uint       { return &u }

// returns a glamour TermRenderer configured with the current theme
func GetMarkdownRenderer(width int, backgroundColor compat.AdaptiveColor) *glamour.TermRenderer {
	r, _ := glamour.NewTermRenderer(
		glamour.WithStyles(generateMarkdownStyleConfig(backgroundColor)),
		glamour.WithWordWrap(width),
		glamour.WithChromaFormatter("terminal16m"),
	)
	return r
}

// creates an ansi.StyleConfig for markdown rendering
// using adaptive colors from the provided theme.
func generateMarkdownStyleConfig(backgroundColor compat.AdaptiveColor) ansi.StyleConfig {
	t := theme.CurrentTheme()
	background := AdaptiveColorToString(backgroundColor)

	darkTheme := styles.DefaultStyles["dark"]
	return ansi.StyleConfig{
		Document: ansi.StyleBlock{
			StylePrimitive: ansi.StylePrimitive{
				BlockPrefix:     "",
				BlockSuffix:     "",
				BackgroundColor: background,
				Color:           AdaptiveColorToString(t.MarkdownText()),
			},
		},
		BlockQuote: ansi.StyleBlock{
			StylePrimitive: ansi.StylePrimitive{
				Color:  AdaptiveColorToString(t.MarkdownBlockQuote()),
				Italic: boolPtr(true),
				Prefix: "┃ ",
			},
			Indent:      uintPtr(1),
			IndentToken: stringPtr(" "),
		},
		List: ansi.StyleList{
			LevelIndent: defaultMargin,
			StyleBlock: ansi.StyleBlock{
				IndentToken: stringPtr(" "),
				StylePrimitive: ansi.StylePrimitive{
					Color: AdaptiveColorToString(t.MarkdownText()),
				},
			},
		},
		Heading: darkTheme.Heading,
		H1:      darkTheme.H1,
		H2:      darkTheme.H2,
		H3:      darkTheme.H3,
		H4:      darkTheme.H4,
		H5:      darkTheme.H5,
		H6:      darkTheme.H6,
		Strikethrough: ansi.StylePrimitive{
			CrossedOut: boolPtr(true),
			Color:      AdaptiveColorToString(t.TextMuted()),
		},
		Emph: ansi.StylePrimitive{
			Color:  AdaptiveColorToString(t.MarkdownEmph()),
			Italic: boolPtr(true),
		},
		Strong: ansi.StylePrimitive{
			Bold:  boolPtr(true),
			Color: AdaptiveColorToString(t.MarkdownStrong()),
		},
		HorizontalRule: ansi.StylePrimitive{
			Color:  AdaptiveColorToString(t.MarkdownHorizontalRule()),
			Format: "\n─────────────────────────────────────────\n",
		},
		Item: ansi.StylePrimitive{
			BlockPrefix: "• ",
			Color:       AdaptiveColorToString(t.MarkdownListItem()),
		},
		Enumeration: ansi.StylePrimitive{
			BlockPrefix: ". ",
			Color:       AdaptiveColorToString(t.MarkdownListEnumeration()),
		},
		Task: ansi.StyleTask{
			Ticked:   "[✓] ",
			Unticked: "[ ] ",
		},
		Link: ansi.StylePrimitive{
			Color:     AdaptiveColorToString(t.MarkdownLink()),
			Underline: boolPtr(true),
		},
		LinkText: ansi.StylePrimitive{
			Color: AdaptiveColorToString(t.MarkdownLinkText()),
			Bold:  boolPtr(true),
		},
		Image: darkTheme.Image,
		ImageText: ansi.StylePrimitive{
			Color:  AdaptiveColorToString(t.MarkdownImageText()),
			Format: "{{.text}}",
		},
		Code: ansi.StyleBlock{
			StylePrimitive: ansi.StylePrimitive{
				BackgroundColor: background,
				Color:           AdaptiveColorToString(t.MarkdownCode()),
				Prefix:          "",
				Suffix:          "",
			},
		},
		CodeBlock: ansi.StyleCodeBlock{
			StyleBlock: ansi.StyleBlock{
				StylePrimitive: ansi.StylePrimitive{
					BackgroundColor: background,
					Prefix:          " ",
					Color:           AdaptiveColorToString(t.MarkdownCodeBlock()),
				},
			},
			Chroma: &ansi.Chroma{
				Background: ansi.StylePrimitive{
					BackgroundColor: background,
				},
				Text: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.MarkdownText()),
				},
				Error: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.Error()),
				},
				Comment: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxComment()),
				},
				CommentPreproc: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxKeyword()),
				},
				Keyword: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxKeyword()),
				},
				KeywordReserved: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxKeyword()),
				},
				KeywordNamespace: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxKeyword()),
				},
				KeywordType: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxType()),
				},
				Operator: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxOperator()),
				},
				Punctuation: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxPunctuation()),
				},
				Name: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxVariable()),
				},
				NameBuiltin: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxVariable()),
				},
				NameTag: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxKeyword()),
				},
				NameAttribute: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxFunction()),
				},
				NameClass: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxType()),
				},
				NameConstant: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxVariable()),
				},
				NameDecorator: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxFunction()),
				},
				NameFunction: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxFunction()),
				},
				LiteralNumber: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxNumber()),
				},
				LiteralString: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxString()),
				},
				LiteralStringEscape: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.SyntaxKeyword()),
				},
				GenericDeleted: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.DiffRemoved()),
				},
				GenericEmph: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.MarkdownEmph()),
					Italic:          boolPtr(true),
				},
				GenericInserted: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.DiffAdded()),
				},
				GenericStrong: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.MarkdownStrong()),
					Bold:            boolPtr(true),
				},
				GenericSubheading: ansi.StylePrimitive{
					BackgroundColor: background,
					Color:           AdaptiveColorToString(t.MarkdownHeading()),
				},
			},
		},
		Table: ansi.StyleTable{
			StyleBlock: ansi.StyleBlock{
				StylePrimitive: ansi.StylePrimitive{
					BlockSuffix:     "",
					BlockPrefix:     "",
					BackgroundColor: stringPtr(""),
					Color:           AdaptiveColorToString(t.MarkdownText()),
				},
			},
			CenterSeparator: stringPtr("┼"),
			ColumnSeparator: stringPtr("│"),
			RowSeparator:    stringPtr("─"),
		},
		DefinitionDescription: ansi.StylePrimitive{
			BlockPrefix: "\n ❯ ",
			Color:       AdaptiveColorToString(t.MarkdownLinkText()),
		},
		Text: ansi.StylePrimitive{
			Color: AdaptiveColorToString(t.MarkdownText()),
		},
		Paragraph: ansi.StyleBlock{
			StylePrimitive: ansi.StylePrimitive{
				Color: AdaptiveColorToString(t.MarkdownText()),
			},
		},
	}
}

// AdaptiveColorToString converts a compat.AdaptiveColor to the appropriate
// hex color string based on the current terminal background
func AdaptiveColorToString(color compat.AdaptiveColor) *string {
	if _, ok := color.Dark.(lipgloss.NoColor); ok {
		return nil
	}
	c1, _ := colorful.MakeColor(color.Dark)
	return stringPtr(c1.Hex())

}
