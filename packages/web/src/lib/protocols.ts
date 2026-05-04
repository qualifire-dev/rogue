import type { AuthType, Protocol, Transport } from "@/api/types";

/**
 * Mirrors `getTransportsForProtocol` in
 * packages/tui/internal/tui/eval_types.go:523-537. Values match the server's
 * lowercase Protocol/Transport enums.
 *
 * - `python` has no transport field at all (the form skips it entirely).
 * - The first entry is the default that should be auto-selected when the
 *   protocol changes.
 */
export function getTransportsForProtocol(protocol: Protocol): Transport[] {
  switch (protocol) {
    case "mcp":
      return ["streamable_http", "sse"];
    case "a2a":
      return ["http"];
    case "openai_api":
      return ["chat_completions"];
    case "python":
      return [];
  }
}

export function protocolNeedsAgentUrl(protocol: Protocol): boolean {
  return protocol !== "python";
}

export function authNeedsCredentials(auth: AuthType): boolean {
  return auth !== "no_auth";
}
