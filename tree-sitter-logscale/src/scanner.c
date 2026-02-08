/**
 * External scanner for tree-sitter-logscale.
 *
 * Handles the regex-vs-division slash disambiguation:
 * - A `/` at the start of input or after operators/keywords begins a regex.
 * - A `/` after an expression (identifier, number, `)`, `]`) is division.
 */

#include "tree_sitter/parser.h"

#include <stdbool.h>
#include <string.h>

enum TokenType {
  REGEX_START,
};

// Check if a character can end an expression (meaning `/` after it is division)
static bool is_expression_end_char(int32_t c) {
  // Identifiers: letters, digits, _, field name chars
  if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
      (c >= '0' && c <= '9') || c == '_' || c == '.' || c == '#' ||
      c == '%' || c == '&' || c == '@' || c == '\\' || c == '^') {
    return true;
  }
  // Closing brackets/parens
  if (c == ')' || c == ']') {
    return true;
  }
  // Closing quote
  if (c == '"') {
    return true;
  }
  return false;
}

void *tree_sitter_logscale_external_scanner_create(void) {
  return NULL;
}

void tree_sitter_logscale_external_scanner_destroy(void *payload) {
  // Nothing to free
}

unsigned tree_sitter_logscale_external_scanner_serialize(void *payload,
                                                         char *buffer) {
  return 0;
}

void tree_sitter_logscale_external_scanner_deserialize(void *payload,
                                                        const char *buffer,
                                                        unsigned length) {
  // Nothing to restore
}

bool tree_sitter_logscale_external_scanner_scan(void *payload,
                                                 TSLexer *lexer,
                                                 const bool *valid_symbols) {
  if (!valid_symbols[REGEX_START]) {
    return false;
  }

  // We need to determine if the current `/` should start a regex.
  // The lexer is positioned at the next non-whitespace character.

  // Skip whitespace (but not newlines for comment detection)
  while (lexer->lookahead == ' ' || lexer->lookahead == '\t' ||
         lexer->lookahead == '\r' || lexer->lookahead == '\f') {
    lexer->advance(lexer, true);
  }

  // Check if we're looking at a `/`
  if (lexer->lookahead != '/') {
    return false;
  }

  // Peek ahead: if next char is also `/`, this is a comment, not a regex
  lexer->mark_end(lexer);
  lexer->advance(lexer, false);
  if (lexer->lookahead == '/') {
    return false; // This is a comment `//`
  }

  // If we got here, we have a single `/` that could be regex start.
  // The tree-sitter parser will only offer REGEX_START as a valid symbol
  // in contexts where a regex is grammatically valid (filters, match guards, etc.)
  // but NOT after expressions where `/` would be division.
  // So if valid_symbols[REGEX_START] is true, we accept it.

  lexer->result_symbol = REGEX_START;
  lexer->mark_end(lexer);
  return true;
}
