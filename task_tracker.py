#!/usr/bin/env python3
"""
Task Tracker CLI - Command-line task manager with Neo4j storage and GitHub sync.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Optional

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Warning: neo4j driver not installed. Install with: pip install neo4j")

VERSION = "0.1.0"


class TaskTracker:
    """Task tracker with Neo4j storage."""

    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None

        if NEO4J_AVAILABLE:
            try:
                self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
                # Test connection
                self.driver.verify_connectivity()
                print(f"✅ Connected to Neo4j at {self.uri}")
            except Exception as e:
                print(f"⚠️  Neo4j connection failed: {e}")
                self.driver = None

    def close(self):
        """Close database connection."""
        if self.driver:
            self.driver.close()

    def add_task(self, title: str, tags: list[str] = None, priority: str = "medium"):
        """Add a new task."""
        if not self.driver:
            print("❌ No database connection")
            return False

        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    CREATE (t:Task {
                        title: $title,
                        status: 'todo',
                        priority: $priority,
                        created: datetime(),
                        tags: $tags
                    })
                    RETURN id(t) as id
                    """,
                    title=title, priority=priority, tags=tags or []
                )
                task_id = result.single()["id"]
                print(f"✅ Task #{task_id} created: {title}")
                return task_id
        except Exception as e:
            print(f"❌ Failed to create task: {e}")
            return False

    def list_tasks(self, status: str = None):
        """List all tasks."""
        if not self.driver:
            print("❌ No database connection")
            return

        try:
            with self.driver.session() as session:
                if status:
                    result = session.run(
                        "MATCH (t:Task {status: $status}) RETURN t ORDER BY t.created DESC",
                        status=status
                    )
                else:
                    result = session.run("MATCH (t:Task) RETURN t ORDER BY t.created DESC")

                tasks = [record["t"] for record in result]

                if not tasks:
                    print("No tasks found.")
                    return

                print(f"\n📋 Tasks ({len(tasks)} total):")
                print("-" * 60)
                for task in tasks:
                    tags = ", ".join(task.get("tags", []))
                    print(f"  #{task.element_id} [{task.get('status', '?').upper()}] {task.get('title', 'No title')}")
                    if tags:
                        print(f"      Tags: {tags} | Priority: {task.get('priority', 'medium')}")
                print()
        except Exception as e:
            print(f"❌ Failed to list tasks: {e}")

    def update_task(self, task_id: str, status: str = None):
        """Update task status."""
        if not self.driver:
            print("❌ No database connection")
            return

        try:
            with self.driver.session() as session:
                if status:
                    result = session.run(
                        "MATCH (t:Task) WHERE elementId(t) = $id SET t.status = $status RETURN t",
                        id=task_id, status=status
                    )
                else:
                    print("❌ No updates specified")
                    return

                if result.single():
                    print(f"✅ Task #{task_id} updated to {status}")
                else:
                    print(f"❌ Task #{task_id} not found")
        except Exception as e:
            print(f"❌ Failed to update task: {e}")

    def delete_task(self, task_id: str):
        """Delete a task."""
        if not self.driver:
            print("❌ No database connection")
            return

        try:
            with self.driver.session() as session:
                result = session.run(
                    "MATCH (t:Task) WHERE elementId(t) = $id DELETE t RETURN count(t) as count",
                    id=task_id
                )
                count = result.single()["count"]
                if count > 0:
                    print(f"✅ Task #{task_id} deleted")
                else:
                    print(f"❌ Task #{task_id} not found")
        except Exception as e:
            print(f"❌ Failed to delete task: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Task Tracker CLI")
    parser.add_argument("--version", action="version", version=f"task-tracker {VERSION}")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title", help="Task title")
    add_parser.add_argument("--tag", action="append", dest="tags", help="Task tags")
    add_parser.add_argument("--priority", choices=["low", "medium", "high"], default="medium", help="Task priority")

    # List command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--status", choices=["todo", "in-progress", "done"], help="Filter by status")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update a task")
    update_parser.add_argument("id", help="Task ID")
    update_parser.add_argument("--status", choices=["todo", "in-progress", "done"], required=True, help="New status")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("id", help="Task ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    tracker = TaskTracker()

    try:
        if args.command == "add":
            tracker.add_task(args.title, args.tags, args.priority)
        elif args.command == "list":
            tracker.list_tasks(args.status)
        elif args.command == "update":
            tracker.update_task(args.id, args.status)
        elif args.command == "delete":
            tracker.delete_task(args.id)
    finally:
        tracker.close()


if __name__ == "__main__":
    main()
