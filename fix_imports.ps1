# Fix all agent imports
Write-Host "🔧 Fixing all agent imports..." -ForegroundColor Cyan

$agents = @(
    "product_interpreter_agent.py",
    "frontend_engineer_agent.py",
    "backend_engineer_agent.py",
    "integration_agent.py",
    "testing_agent.py",
    "debug_agent.py",
    "security_agent.py",
    "production_readiness_agent.py"
)

foreach ($agent in $agents) {
    $file = "agents\$agent"
    Write-Host "  Fixing $agent..." -ForegroundColor Yellow
    
    # Read content
    $content = Get-Content $file -Raw
    
    # Fix base_agent import
    $content = $content -replace 'from base_agent import', 'from agents.base_agent import'
    
    # Fix typing imports - ensure Optional is included
    $content = $content -replace 'from typing import ([^O]*?)(\r?\n)', 'from typing import $1, Optional$2'
    $content = $content -replace ', Optional, Optional', ', Optional'  # Remove duplicates
    
    # Write back
    Set-Content $file -Value $content -NoNewline
}

Write-Host "✅ All agent imports fixed!" -ForegroundColor Green
