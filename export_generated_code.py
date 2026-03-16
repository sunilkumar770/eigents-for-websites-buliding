import sqlite3
import json
import os
import sys

def export_project_code(db_path, project_id, output_base_dir="generated_projects"):
    """Export code files from the workflow state database."""
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all stages for the project
    cursor.execute("""
        SELECT stage_name, outputs
        FROM stages
        WHERE project_id = ? AND status = 'completed'
    """, (project_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print(f"No completed stages found for project {project_id}")
        return

    project_dir = os.path.join(output_base_dir, project_id)
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
        print(f"Created project directory: {project_dir}")

    exported_files = 0
    
    for stage_name, outputs_json in rows:
        try:
            outputs = json.loads(outputs_json)
        except json.JSONDecodeError:
            print(f"Failed to parse outputs for {stage_name}")
            continue
            
        # Check for code_files in outputs
        if 'code_files' in outputs:
            print(f"Exporting files from stage: {stage_name}")
            
            # Determine subfolder based on stage
            subfolder = ""
            if "frontend" in stage_name:
                subfolder = "frontend"
            elif "backend" in stage_name:
                subfolder = "backend"
            
            target_dir = os.path.join(project_dir, subfolder)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            for file_path, content in outputs['code_files'].items():
                # Handle potential relative paths in file_path
                full_path = os.path.join(target_dir, file_path)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"  Saved: {full_path}")
                exported_files += 1
                
    print(f"\nExport complete. {exported_files} files written to {project_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_generated_code.py <project_id>")
        # Try to find the most recent project
        conn = sqlite3.connect("workflow_state.db")
        cursor = conn.cursor()
        cursor.execute("SELECT project_id FROM workflows ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            print(f"Auto-selecting most recent project: {row[0]}")
            export_project_code("workflow_state.db", row[0])
        else:
            sys.exit(1)
    else:
        export_project_code("workflow_state.db", sys.argv[1])
