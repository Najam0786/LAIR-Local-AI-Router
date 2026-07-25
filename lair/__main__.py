import argparse
import asyncio
import sys

from app.hardware.tier import HardwareTier
from lair.commands import community as community_command
from lair.commands import doctor as doctor_command
from lair.commands import install as install_command
from lair.commands import memory as memory_command
from lair.commands import voice as voice_command


def main() -> None:
    parser = argparse.ArgumentParser(prog="lair")
    subparsers = parser.add_subparsers(dest="command")

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Profile this machine and recommend a model portfolio.",
    )
    doctor_parser.add_argument(
        "--init",
        action="store_true",
        help="Save the recommended portfolio as configs/active_portfolio.yaml.",
    )

    install_parser = subparsers.add_parser(
        "install",
        help="Point IDE clients (Continue, ...) at LAIR's endpoint.",
    )
    install_parser.add_argument(
        "--client",
        default=None,
        help="Install into one specific client (e.g. continue). "
        "Omit to auto-detect and install into all supported clients.",
    )
    install_parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Restore the client's config from LAIR's backup instead of installing.",
    )
    install_parser.add_argument(
        "--base-url",
        default=None,
        help="Override LAIR's endpoint URL (default: derived from Settings).",
    )

    memory_parser = subparsers.add_parser(
        "memory",
        help="Inspect or manage persistent project memory (I-18).",
    )
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command")

    memory_list_parser = memory_subparsers.add_parser("list", help="List memories for a project scope.")
    memory_list_parser.add_argument("scope")

    memory_show_parser = memory_subparsers.add_parser("show", help="Show one memory by id.")
    memory_show_parser.add_argument("memory_id")

    memory_forget_parser = memory_subparsers.add_parser("forget", help="Forget one memory by id, or wipe a whole scope.")
    memory_forget_parser.add_argument("target")
    memory_forget_parser.add_argument(
        "--scope",
        action="store_true",
        help="Treat the target as a project scope and wipe every memory in it, instead of a single memory id.",
    )

    memory_export_parser = memory_subparsers.add_parser("export", help="Export a project scope's memories as JSON.")
    memory_export_parser.add_argument("scope")

    voice_parser = subparsers.add_parser(
        "voice",
        help="File-based voice round trip against a running LAIR server (I-11).",
    )
    voice_parser.add_argument("--input", required=True, help="Path to an input audio file (e.g. WAV).")
    voice_parser.add_argument("--output", required=True, help="Path to write the synthesized reply audio.")
    voice_parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    voice_parser.add_argument("--project-scope", default=None)

    community_parser = subparsers.add_parser(
        "community",
        help="Export this machine's anonymized benchmark scores (I-12).",
    )
    community_subparsers = community_parser.add_subparsers(dest="community_command")
    community_export_parser = community_subparsers.add_parser("export", help="Print an anonymized JSON export.")
    community_export_parser.add_argument(
        "--tier",
        required=True,
        choices=[t.value for t in HardwareTier],
        help="This machine's hardware tier, as reported by `lair doctor`.",
    )

    args = parser.parse_args()

    if args.command == "community":
        if args.community_command == "export":
            print(community_command.export(HardwareTier(args.tier)))
        else:
            community_parser.print_help()
            sys.exit(1)
        return

    if args.command == "voice":
        reply_text = voice_command.run(
            input_path=args.input,
            output_path=args.output,
            base_url=args.base_url,
            project_scope=args.project_scope,
        )
        print(reply_text)
        return

    if args.command == "memory":
        if args.memory_command == "list":
            print(memory_command.list_memories(args.scope))
        elif args.memory_command == "show":
            print(memory_command.show_memory(args.memory_id))
        elif args.memory_command == "forget":
            if args.scope:
                print(memory_command.wipe_scope(args.target))
            else:
                print(memory_command.forget_memory(args.target))
        elif args.memory_command == "export":
            print(memory_command.export_scope(args.scope))
        else:
            memory_parser.print_help()
            sys.exit(1)
        return

    if args.command == "doctor":
        asyncio.run(doctor_command.run(init=args.init))
        return

    if args.command == "install":
        install_command.run(
            client=args.client,
            uninstall=args.uninstall,
            base_url=args.base_url,
        )
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
