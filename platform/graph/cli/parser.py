import re
import shlex
from typing import Optional
from graph.facade.facade import PlatformFacade
from graph.cli.commands import (
    Command, CreateNodeCommand, EditNodeCommand, DeleteNodeCommand,
    CreateEdgeCommand, EditEdgeCommand, DeleteEdgeCommand,
    SearchCommand, FilterCommand, ClearCommand, ResetCommand,
)

HELP_TEXT = """Available commands:
  create node --id=<id> [--property <key>=<value> ...]
  create edge --id=<edge_id> [--property <key>=<value> ...] <source_id> <target_id>
  edit node --id=<id> --property <key>=<value> [--property <key>=<value> ...]
  edit edge --id=<edge_id> --property <key>=<value> [--property <key>=<value> ...]
  delete node --id=<id>
  delete edge --id=<edge_id>
  search '<text>'
  filter '<attribute> <operator> <value>'
  reset
  clear
  help
"""


class CLIParser:
    """
    Parses a command string and returns the appropriate Command object.
    All commands operate on the active graph via PlatformFacade.
    """

    def __init__(self, facade: PlatformFacade):
        self.facade = facade

    def parse(self, raw: str) -> Optional[Command]:
        """
        Parse raw command string into a Command object.
        Returns None for empty input.
        Raises ValueError for unknown or malformed commands.
        """
        raw = raw.strip()
        if not raw:
            return None

        # tokenize (respects quoted strings)
        try:
            tokens = shlex.split(raw)
        except ValueError as e:
            raise ValueError(f"Parse error: {e}")

        verb = tokens[0].lower()

        if verb == "help":
            return self._help_command()
        elif verb == "create":
            return self._parse_create(tokens)
        elif verb == "edit":
            return self._parse_edit(tokens)
        elif verb == "delete":
            return self._parse_delete(tokens)
        elif verb == "search":
            return self._parse_search(tokens)
        elif verb == "filter":
            return self._parse_filter(tokens)
        elif verb == "clear":
            return ClearCommand(self.facade)
        elif verb == "reset":
            return ResetCommand(self.facade)
        else:
            raise ValueError(f"Unknown command: '{verb}'. Type 'help' for available commands.")

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def _parse_create(self, tokens: list) -> Command:
        if len(tokens) < 2:
            raise ValueError("Usage: create node|edge ...")
        target = tokens[1].lower()

        if target == "node":
            node_id = self._require_flag(tokens, "--id")
            attrs = self._parse_properties(tokens)
            return CreateNodeCommand(self.facade, node_id, attrs)

        elif target == "edge":
            # positional: last two tokens are source and target node ids
            positional = self._positional_args(tokens)
            if len(positional) < 2:
                raise ValueError("Usage: create edge --id=<id> [--property ...] <source_id> <target_id>")
            source_id, target_id = positional[0], positional[1]
            label = self._optional_flag(tokens, "--label") or ""
            attrs = self._parse_properties(tokens)
            return CreateEdgeCommand(self.facade, source_id, target_id, label, attrs)

        raise ValueError(f"Unknown create target: '{target}'. Use 'node' or 'edge'.")

    # ------------------------------------------------------------------
    # Edit
    # ------------------------------------------------------------------

    def _parse_edit(self, tokens: list) -> Command:
        if len(tokens) < 2:
            raise ValueError("Usage: edit node|edge ...")
        target = tokens[1].lower()

        if target == "node":
            node_id = self._require_flag(tokens, "--id")
            attrs = self._parse_properties(tokens)
            if not attrs:
                raise ValueError("edit node requires at least one --property key=value")
            return EditNodeCommand(self.facade, node_id, attrs)

        elif target == "edge":
            edge_id = self._require_flag(tokens, "--id")
            attrs = self._parse_properties(tokens)
            if not attrs:
                raise ValueError("edit edge requires at least one --property key=value")
            return EditEdgeCommand(self.facade, edge_id, attrs)

        raise ValueError(f"Unknown edit target: '{target}'. Use 'node' or 'edge'.")

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def _parse_delete(self, tokens: list) -> Command:
        if len(tokens) < 2:
            raise ValueError("Usage: delete node|edge ...")
        target = tokens[1].lower()

        if target == "node":
            node_id = self._require_flag(tokens, "--id")
            return DeleteNodeCommand(self.facade, node_id)

        elif target == "edge":
            edge_id = self._require_flag(tokens, "--id")
            return DeleteEdgeCommand(self.facade, edge_id)

        raise ValueError(f"Unknown delete target: '{target}'. Use 'node' or 'edge'.")

    # ------------------------------------------------------------------
    # Search & Filter
    # ------------------------------------------------------------------

    def _parse_search(self, tokens: list) -> Command:
        if len(tokens) < 2:
            raise ValueError("Usage: search '<text>'")
        return SearchCommand(self.facade, tokens[1])

    def _parse_filter(self, tokens: list) -> Command:
        if len(tokens) < 2:
            raise ValueError("Usage: filter '<attribute> <operator> <value>'")
        return FilterCommand(self.facade, tokens[1])

    # ------------------------------------------------------------------
    # Help
    # ------------------------------------------------------------------

    def _help_command(self):
        """Returns a command that just prints help text."""
        facade = self.facade

        class HelpCommand(Command):
            def execute(self):
                return HELP_TEXT

        return HelpCommand(facade)

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------

    def _require_flag(self, tokens: list, flag: str) -> str:
        """Extract required --flag=value. Raises ValueError if missing."""
        for token in tokens:
            if token.startswith(f"{flag}="):
                return token[len(flag) + 1:]
        raise ValueError(f"Missing required flag: {flag}")

    def _optional_flag(self, tokens: list, flag: str) -> Optional[str]:
        """Extract optional --flag=value. Returns None if missing."""
        for token in tokens:
            if token.startswith(f"{flag}="):
                return token[len(flag) + 1:]
        return None

    def _parse_properties(self, tokens: list) -> dict:
        """
        Extract all --property key=value pairs.
        Returns dict of {key: value_string}.
        """
        props = {}
        i = 0
        while i < len(tokens):
            if tokens[i] == "--property" and i + 1 < len(tokens):
                kv = tokens[i + 1]
                if "=" not in kv:
                    raise ValueError(f"Invalid property format '{kv}'. Expected key=value.")
                k, v = kv.split("=", 1)
                props[k.strip()] = v.strip()
                i += 2
            else:
                i += 1
        return props

    def _positional_args(self, tokens: list) -> list:
        """
        Return tokens that are not flags (don't start with --).
        Skip first two tokens (verb + target).
        """
        result = []
        skip_next = False
        for token in tokens[2:]:
            if skip_next:
                skip_next = False
                continue
            if token == "--property":
                skip_next = True
                continue
            if token.startswith("--"):
                continue
            result.append(token)
        return result