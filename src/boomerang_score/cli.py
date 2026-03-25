#!/usr/bin/env python3
"""
Command-line interface for boomerang scoring.

Provides commands to manage competitions, add participants, update results,
and export reports without needing the GUI.
"""

import sys
import argparse
import csv
from pathlib import Path
from boomerang_score.core import Competition, ACC, AUS, MTA, END, FC, TC, TIMED
from boomerang_score.services import CompetitionService, ExportService

DISCIPLINES = [ACC, AUS, MTA, END, FC, TC, TIMED]


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Boomerang Scoring CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add participant command
    add_parser = subparsers.add_parser("add", help="Add a participant")
    add_parser.add_argument("name", help="Participant name")
    add_parser.add_argument("--startnumber", type=int, help="Start number (auto if not specified)")
    add_parser.add_argument("--acc", type=float, default=0.0, help="Accuracy result")
    add_parser.add_argument("--aus", type=float, default=0.0, help="Aussie Round result")
    add_parser.add_argument("--mta", type=float, default=0.0, help="MTA result")
    add_parser.add_argument("--end", type=float, default=0.0, help="Endurance result")
    add_parser.add_argument("--fc", type=float, default=0.0, help="Fast Catch result")
    add_parser.add_argument("--tc", type=float, default=0.0, help="Trick Catch result")
    add_parser.add_argument("--timed", type=float, default=0.0, help="Timed result")

    # List participants command
    list_parser = subparsers.add_parser("list", help="List all participants")
    list_parser.add_argument("--sort", choices=["name", "rank", "startnumber"],
                            default="rank", help="Sort by field")

    # Export commands
    export_parser = subparsers.add_parser("export", help="Export results")
    export_parser.add_argument("format", choices=["csv", "pdf"], help="Export format")
    export_parser.add_argument("output", help="Output file path")

    # Set active disciplines
    disc_parser = subparsers.add_parser("disciplines", help="Set active disciplines")
    disc_parser.add_argument("codes", nargs="+",
                            choices=["acc", "aus", "mta", "end", "fc", "tc", "timed"],
                            help="Discipline codes to activate")

    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize competition and services
    competition = Competition(title="CLI Competition")
    service = CompetitionService(competition, DISCIPLINES)
    export_service = ExportService(competition, DISCIPLINES)

    # Set default active disciplines
    service.set_active_disciplines({"acc", "aus", "mta"})

    try:
        if args.command == "add":
            # Add participant
            disc_results = {
                "acc": args.acc,
                "aus": args.aus,
                "mta": args.mta,
                "end": args.end,
                "fc": args.fc,
                "tc": args.tc,
                "timed": args.timed,
            }

            startnr = args.startnumber if args.startnumber else competition.next_free_startnumber()

            participant = service.add_participant(args.name, startnr, disc_results)

            print(f"Added participant: {participant.name} (Start #{participant.startnumber})")
            points_str = f"{participant.total_points:.2f}" if participant.total_points else "0.00"
            print(f"  Total Points: {points_str}")
            print(f"  Overall Rank: {participant.overall_rank or '-'}")

        elif args.command == "list":
            # List participants
            participants = competition.get_all_participants()

            if not participants:
                print("No participants yet.")
                return 0

            # Sort participants
            if args.sort == "name":
                participants.sort(key=lambda p: p.name)
            elif args.sort == "rank":
                participants.sort(key=lambda p: (p.overall_rank or 999, p.name))
            elif args.sort == "startnumber":
                participants.sort(key=lambda p: p.startnumber)

            # Print table header
            print(f"{'Rank':<6} {'#':<6} {'Name':<30} {'Points':<10}")
            print("-" * 52)

            # Print participants
            for p in participants:
                rank_str = str(p.overall_rank) if p.overall_rank else "-"
                points_str = f"{p.total_points:.2f}" if p.total_points else "-"
                print(f"{rank_str:<6} {p.startnumber:<6} {p.name:<30} {points_str:<10}")

        elif args.command == "export":
            # Export results
            if not competition.get_all_participants():
                print("Error: No participants to export")
                return 1

            output_path = Path(args.output)
            participant_order = sorted(
                competition.participants.keys(),
                key=lambda startnr: (competition.get_participant(startnr).overall_rank or 999,
                                   competition.get_participant(startnr).name)
            )

            if args.format == "csv":
                columns = ["name", "startnumber", "total", "overall_rank"]
                for d in DISCIPLINES:
                    if competition.is_discipline_active(d.code):
                        columns.extend([f"{d.code}_res", f"{d.code}_pts", f"{d.code}_rank"])

                headers = {
                    "name": "Name",
                    "startnumber": "Start #",
                    "total": "Total Points",
                    "overall_rank": "Rank",
                }
                for d in DISCIPLINES:
                    if competition.is_discipline_active(d.code):
                        headers[f"{d.code}_res"] = f"{d.label} Result"
                        headers[f"{d.code}_pts"] = f"{d.label} Points"
                        headers[f"{d.code}_rank"] = f"{d.label} Rank"

                export_service.export_csv(str(output_path), columns, headers, participant_order)
                print(f"Exported CSV to: {output_path}")

            elif args.format == "pdf":
                export_service.export_pdf_full_list(str(output_path), participant_order)
                print(f"Exported PDF to: {output_path}")

        elif args.command == "disciplines":
            # Set active disciplines
            service.set_active_disciplines(set(args.codes))
            print(f"Active disciplines: {', '.join(args.codes).upper()}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
