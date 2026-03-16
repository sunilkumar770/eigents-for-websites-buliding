"""
CLI Tool

Command-line interface for the multi-agent system.
"""

import click
import requests
import json
import time
from typing import Optional
from datetime import datetime


API_BASE_URL = "http://localhost:8000"


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Multi-Agent Web Development System CLI"""
    pass


@cli.command()
@click.argument('prompt')
@click.option('--context', '-c', help='Additional context as JSON string')
@click.option('--watch', '-w', is_flag=True, help='Watch progress in real-time')
def create(prompt: str, context: Optional[str], watch: bool):
    """
    Create a new project from a prompt.
    
    Example:
        antigravity create "Build a recipe sharing app"
    """
    try:
        # Parse context if provided
        context_dict = json.loads(context) if context else None
        
        # Create project
        response = requests.post(
            f"{API_BASE_URL}/projects",
            json={
                'prompt': prompt,
                'context': context_dict
            }
        )
        response.raise_for_status()
        
        project = response.json()
        project_id = project['project_id']
        
        click.echo(click.style("✅ Project created!", fg="green", bold=True))
        click.echo(f"Project ID: {project_id}")
        click.echo(f"Status: {project['status']}")
        click.echo(f"Current Stage: {project['current_stage']}")
        
        if watch:
            click.echo("\n🔄 Watching progress...\n")
            watch_progress(project_id)
    
    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"), err=True)
        exit(1)
    except json.JSONDecodeError:
        click.echo(click.style("❌ Invalid JSON in context", fg="red"), err=True)
        exit(1)


@cli.command()
@click.argument('project_id')
def status(project_id: str):
    """
    Get project status.
    
    Example:
        antigravity status abc-123
    """
    try:
        response = requests.get(f"{API_BASE_URL}/projects/{project_id}")
        response.raise_for_status()
        
        status = response.json()
        
        click.echo(click.style(f"\n📊 Project Status", fg="cyan", bold=True))
        click.echo(f"Project ID: {status['project_id']}")
        click.echo(f"Status: {get_status_icon(status['status'])} {status['status']}")
        click.echo(f"Current Stage: {status['current_stage']}")
        click.echo(f"Pending Tasks: {status['pending_tasks']}")
        click.echo(f"Running Tasks: {status['running_tasks']}")
        
        click.echo(f"\n📋 Stages:")
        for stage in status['stages']:
            icon = get_stage_icon(stage['status'])
            click.echo(
                f"  {icon} {stage['name']}: {stage['status']} "
                f"(confidence: {stage['confidence']}%)"
            )
        
        if status['errors']:
            click.echo(click.style(f"\n⚠️ Errors:", fg="yellow"))
            for error in status['errors']:
                click.echo(f"  - {error}")
        
        click.echo(f"\nCreated: {format_timestamp(status['created_at'])}")
        click.echo(f"Updated: {format_timestamp(status['updated_at'])}")
    
    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"), err=True)
        exit(1)


@cli.command()
@click.argument('project_id')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
def logs(project_id: str, follow: bool):
    """
    View project logs.
    
    Example:
        antigravity logs abc-123 --follow
    """
    if follow:
        watch_progress(project_id)
    else:
        # Just show current status
        status_cmd = click.Context(status)
        status_cmd.invoke(status, project_id=project_id)


@cli.command()
@click.argument('project_id')
@click.option('--output', '-o', default='./output', help='Output directory')
def download(project_id: str, output: str):
    """
    Download generated code artifacts.
    
    Example:
        antigravity download abc-123 --output ./my-app
    """
    try:
        response = requests.get(f"{API_BASE_URL}/projects/{project_id}/artifacts")
        response.raise_for_status()
        
        artifacts = response.json()
        
        import os
        
        # Create output directory
        os.makedirs(output, exist_ok=True)
        
        # Save files
        file_count = 0
        for category, files in artifacts.items():
            category_dir = os.path.join(output, category)
            os.makedirs(category_dir, exist_ok=True)
            
            for filename, content in files.items():
                filepath = os.path.join(category_dir, filename)
                
                # Create subdirectories if needed
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                file_count += 1
        
        click.echo(click.style(f"✅ Downloaded {file_count} files to {output}", fg="green"))
    
    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"), err=True)
        exit(1)


@cli.command()
@click.argument('project_id')
@click.argument('stage')
def retry(project_id: str, stage: str):
    """
    Retry a failed stage.
    
    Example:
        antigravity retry abc-123 testing
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/projects/{project_id}/retry",
            json={'stage_name': stage}
        )
        response.raise_for_status()
        
        result = response.json()
        click.echo(click.style(f"✅ {result['message']}", fg="green"))
    
    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"), err=True)
        exit(1)


@cli.command()
@click.option('--status', '-s', help='Filter by status')
@click.option('--limit', '-l', default=10, help='Maximum number of projects')
def list(status: Optional[str], limit: int):
    """
    List all projects.
    
    Example:
        antigravity list --status running
    """
    try:
        params = {'limit': limit}
        if status:
            params['status'] = status
        
        response = requests.get(f"{API_BASE_URL}/projects", params=params)
        response.raise_for_status()
        
        projects = response.json()
        
        if not projects:
            click.echo("No projects found")
            return
        
        click.echo(click.style(f"\n📦 Projects ({len(projects)})", fg="cyan", bold=True))
        
        for project in projects:
            icon = get_status_icon(project['status'])
            click.echo(f"\n{icon} {project['project_id']}")
            click.echo(f"  Status: {project['status']}")
            click.echo(f"  Stage: {project['current_stage']}")
            click.echo(f"  Prompt: {project['prompt'][:60]}...")
            click.echo(f"  Created: {format_timestamp(project['created_at'])}")
    
    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"), err=True)
        exit(1)


@cli.command()
def stats():
    """View system statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        response.raise_for_status()
        
        stats = response.json()
        
        click.echo(click.style("\n📊 System Statistics", fg="cyan", bold=True))
        
        click.echo("\nWorkflows:")
        for key, value in stats['workflows'].items():
            click.echo(f"  {key}: {value}")
        
        click.echo("\nTasks:")
        for key, value in stats['tasks'].items():
            click.echo(f"  {key}: {value}")
        
        click.echo("\nMessages:")
        click.echo(f"  total: {stats['messages']['total_messages']}")
    
    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"), err=True)
        exit(1)


def watch_progress(project_id: str):
    """Watch project progress in real-time"""
    try:
        last_stage = None
        
        while True:
            response = requests.get(f"{API_BASE_URL}/projects/{project_id}")
            response.raise_for_status()
            
            status = response.json()
            
            # Print stage updates
            if status['current_stage'] != last_stage:
                icon = get_stage_icon('running')
                click.echo(f"{icon} {status['current_stage']}...")
                last_stage = status['current_stage']
            
            # Check if complete
            if status['status'] in ['completed', 'failed', 'cancelled']:
                if status['status'] == 'completed':
                    click.echo(click.style("\n🎉 Workflow completed!", fg="green", bold=True))
                else:
                    click.echo(click.style(f"\n❌ Workflow {status['status']}", fg="red", bold=True))
                
                # Show final stages
                click.echo("\nFinal stages:")
                for stage in status['stages']:
                    icon = get_stage_icon(stage['status'])
                    click.echo(
                        f"  {icon} {stage['name']}: {stage['status']} "
                        f"(confidence: {stage['confidence']}%)"
                    )
                
                break
            
            time.sleep(2)
    
    except KeyboardInterrupt:
        click.echo("\n\nStopped watching")
    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"\n❌ Error: {e}", fg="red"), err=True)
        exit(1)


def get_status_icon(status: str) -> str:
    """Get icon for status"""
    icons = {
        'idle': '⏸️',
        'running': '🔄',
        'completed': '✅',
        'failed': '❌',
        'cancelled': '🚫',
        'paused': '⏸️'
    }
    return icons.get(status, '❓')


def get_stage_icon(status: str) -> str:
    """Get icon for stage status"""
    icons = {
        'pending': '⏳',
        'running': '🔄',
        'completed': '✅',
        'failed': '❌',
        'skipped': '⏭️'
    }
    return icons.get(status, '❓')


def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp


if __name__ == '__main__':
    cli()
