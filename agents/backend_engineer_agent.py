"""
Backend Engineer Agent

Generates complete backend applications with APIs, database schemas,
authentication, and business logic.
"""

import json
from typing import Dict, List, Any, Tuple, Optional
from agents.base_agent import BaseAgent, AgentType, AgentResult


class BackendEngineerAgent(BaseAgent):
    """
    Agent responsible for generating backend code.
    
    Inputs:
        - requirements: Product requirements (from Product Interpreter)
        - config: Backend configuration (framework, database, etc.)
    
    Outputs:
        - code_files: Dict of filename -> code content
        - api_specification: OpenAPI 3.0 spec
        - database_schema: Database schema definition
        - migrations: Database migration files
        - setup_instructions: How to run the backend
    """
    
    def __init__(self, llm_adapter: Any, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            agent_type=AgentType.BACKEND_ENGINEER,
            llm_adapter=llm_adapter,
            config=config
        )
        
        # Default backend config
        self.default_config = {
            'backend': 'nodejs',  # nodejs, python, go
            'framework': 'express',  # express, fastapi, gin
            'database': 'postgresql',  # postgresql, mongodb, mysql
            'orm': 'prisma',  # prisma, typeorm, sqlalchemy
            'auth': 'jwt',  # jwt, oauth2, auth0
            'api_style': 'rest',  # rest, graphql
            'validation': True,
            'rate_limiting': True
        }
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input data"""
        errors = []
        
        if 'requirements' not in inputs:
            errors.append("Missing required field: 'requirements'")
        else:
            req = inputs['requirements']
            if not isinstance(req, dict):
                errors.append("Field 'requirements' must be a dictionary")
            elif 'features' not in req:
                errors.append("Requirements must include 'features'")
        
        return len(errors) == 0, errors
    
    def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute backend code generation
        
        Args:
            inputs: Dict with 'requirements' and optional 'config'
        
        Returns:
            AgentResult with generated backend code
        """
        self.logger.info("Starting backend code generation")
        
        requirements = inputs['requirements']
        config = {**self.default_config, **inputs.get('config', {})}
        
        # Step 1: Design API architecture
        self.logger.info("Designing API architecture")
        api_design = self._design_api(requirements, config)
        
        # Step 2: Design database schema
        self.logger.info("Designing database schema")
        db_schema = self._design_database(requirements, config)
        
        # Step 3: Generate code files
        self.logger.info("Generating code files")
        code_files = self._generate_code_files(
            requirements,
            api_design,
            db_schema,
            config
        )
        
        # Step 4: Generate migrations
        migrations = self._generate_migrations(db_schema, config)
        
        # Step 5: Generate API documentation
        api_spec = self._generate_api_spec(api_design, config)
        
        # Step 6: Generate setup instructions
        setup_instructions = self._generate_setup_instructions(config)
        
        # Calculate confidence
        confidence = self._calculate_backend_confidence(
            code_files,
            api_design,
            db_schema,
            requirements
        )
        
        # Log decision
        self.log_decision(
            decision=f"Generated {config['backend']} backend with {len(api_design['endpoints'])} endpoints",
            reasoning=f"Created {len(db_schema['tables'])} database tables, "
                     f"using {config['framework']} framework, "
                     f"confidence: {confidence}%"
        )
        
        return AgentResult(
            success=True,
            confidence=confidence,
            outputs={
                'code_files': code_files,
                'api_design': api_design,
                'database_schema': db_schema,
                'migrations': migrations,
                'api_specification': api_spec,
                'setup_instructions': setup_instructions,
                'config': config
            },
            metadata={
                'backend': config['backend'],
                'framework': config['framework'],
                'database': config['database'],
                'endpoint_count': len(api_design['endpoints']),
                'table_count': len(db_schema['tables'])
            }
        )
    
    def _design_api(
        self,
        requirements: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Design API architecture using LLM"""
        
        prompt = f"""
You are a Senior Backend Engineer. Design a RESTful API for the following application.

Requirements:
{json.dumps(requirements, indent=2)}

Framework: {config['framework']}
Database: {config['database']}
Auth: {config['auth']}

Create an API design in JSON format:

{{
  "endpoints": [
    {{
      "method": "GET|POST|PUT|DELETE",
      "path": "/api/resource",
      "description": "string",
      "auth_required": boolean,
      "request_body": {{}},
      "response": {{}},
      "validation": ["string"]
    }}
  ],
  "controllers": [
    {{
      "name": "string",
      "endpoints": ["string"],
      "dependencies": ["string"]
    }}
  ],
  "middleware": ["auth", "validation", "error-handling", "rate-limiting"]
}}

Include endpoints for:
- Authentication (register, login, logout, refresh)
- CRUD operations for main entities
- Business logic operations

Return ONLY the JSON, no additional text.
"""
        
        response = self._call_llm(prompt, temperature=0.5)
        api_design = self._parse_json_from_llm(response)
        
        if not api_design:
            self.logger.warning("Failed to parse API design, using fallback")
            api_design = self._create_fallback_api_design(requirements)
        
        return api_design
    
    def _create_fallback_api_design(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic fallback API design"""
        return {
            'endpoints': [
                {'method': 'POST', 'path': '/api/auth/register', 'auth_required': False},
                {'method': 'POST', 'path': '/api/auth/login', 'auth_required': False},
                {'method': 'GET', 'path': '/api/health', 'auth_required': False}
            ],
            'controllers': [
                {'name': 'AuthController', 'endpoints': ['/api/auth/*'], 'dependencies': []}
            ],
            'middleware': ['auth', 'validation', 'error-handling']
        }
    
    def _design_database(
        self,
        requirements: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Design database schema using LLM"""
        
        prompt = f"""
You are a Database Architect. Design a database schema for the following application.

Requirements:
{json.dumps(requirements, indent=2)}

Database: {config['database']}

Create a database schema in JSON format:

{{
  "tables": [
    {{
      "name": "string",
      "columns": [
        {{
          "name": "string",
          "type": "string",
          "nullable": boolean,
          "unique": boolean,
          "default": "string|null",
          "references": "table.column|null"
        }}
      ],
      "indexes": ["column_name"],
      "constraints": ["string"]
    }}
  ],
  "relationships": [
    {{
      "from": "table.column",
      "to": "table.column",
      "type": "one-to-one|one-to-many|many-to-many"
    }}
  ]
}}

Include:
- Users table with authentication fields
- Tables for main entities
- Proper foreign keys and indexes
- Timestamps (created_at, updated_at)

Return ONLY the JSON, no additional text.
"""
        
        response = self._call_llm(prompt, temperature=0.5)
        db_schema = self._parse_json_from_llm(response)
        
        if not db_schema:
            self.logger.warning("Failed to parse database schema, using fallback")
            db_schema = self._create_fallback_db_schema()
        
        return db_schema
    
    def _create_fallback_db_schema(self) -> Dict[str, Any]:
        """Create basic fallback database schema"""
        return {
            'tables': [
                {
                    'name': 'users',
                    'columns': [
                        {'name': 'id', 'type': 'uuid', 'nullable': False, 'unique': True},
                        {'name': 'email', 'type': 'string', 'nullable': False, 'unique': True},
                        {'name': 'password', 'type': 'string', 'nullable': False},
                        {'name': 'created_at', 'type': 'timestamp', 'nullable': False}
                    ],
                    'indexes': ['email'],
                    'constraints': []
                }
            ],
            'relationships': []
        }
    
    def _generate_code_files(
        self,
        requirements: Dict[str, Any],
        api_design: Dict[str, Any],
        db_schema: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate all backend code files"""
        
        code_files = {}
        
        # Generate server entry point
        code_files['src/server.js'] = self._generate_server_file(config)
        
        # Generate controllers
        for controller in api_design.get('controllers', []):
            path = f"src/controllers/{controller['name']}.js"
            code_files[path] = self._generate_controller(controller, config)
        
        # Generate models
        for table in db_schema.get('tables', []):
            path = f"src/models/{table['name'].capitalize()}.js"
            code_files[path] = self._generate_model(table, config)
        
        # Generate middleware
        code_files['src/middleware/auth.js'] = self._generate_auth_middleware(config)
        code_files['src/middleware/validation.js'] = self._generate_validation_middleware(config)
        code_files['src/middleware/errorHandler.js'] = self._generate_error_handler(config)
        
        # Generate routes
        code_files['src/routes/index.js'] = self._generate_routes(api_design, config)
        
        # Generate config
        code_files['src/config/database.js'] = self._generate_db_config(config)
        code_files['src/config/env.js'] = self._generate_env_config(config)
        
        # Generate package.json
        code_files['package.json'] = json.dumps(
            self._generate_package_json(config),
            indent=2
        )
        
        # Generate .env.example
        code_files['.env.example'] = self._generate_env_example(config)
        
        # Generate README
        code_files['README.md'] = self._generate_readme(config)
        
        return code_files
    
    def _generate_server_file(self, config: Dict[str, Any]) -> str:
        """Generate main server file"""
        
        if config['backend'] == 'nodejs':
            return """const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const routes = require('./routes');
const errorHandler = require('./middleware/errorHandler');
const { connectDatabase } = require('./config/database');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100 // 100 requests per minute
});
app.use(limiter);

// Routes
app.use('/api', routes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Error handling
app.use(errorHandler);

// Start server
async function start() {
  try {
    await connectDatabase();
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

start();

module.exports = app;
"""
        elif config['backend'] == 'python':
            return """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
from .routes import router
from .config.database import init_db

app = FastAPI(title="API", version="1.0.0")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.on_event("startup")
async def startup():
    await init_db()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
        else:
            return "// Go server implementation"
    
    def _generate_controller(self, controller: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate controller code"""
        
        prompt = f"""
Generate a {config['framework']} controller for:

Controller: {controller['name']}
Endpoints: {controller.get('endpoints', [])}

Include:
- Input validation
- Error handling
- Async/await patterns
- Proper HTTP status codes

Return ONLY the code, no explanations.
"""
        
        code = self._call_llm(prompt, temperature=0.3, max_tokens=2048)
        return self._clean_code(code)
    
    def _generate_model(self, table: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate database model"""
        
        if config['orm'] == 'prisma':
            columns = '\n  '.join([
                f"{col['name']} {col['type']}" + 
                (' @unique' if col.get('unique') else '') +
                (' @default(now())' if col.get('default') == 'now()' else '')
                for col in table['columns']
            ])
            
            return f"""model {table['name'].capitalize()} {{
  {columns}
}}
"""
        else:
            return f"// Model for {table['name']}"
    
    def _generate_auth_middleware(self, config: Dict[str, Any]) -> str:
        """Generate authentication middleware"""
        
        return """const jwt = require('jsonwebtoken');

module.exports = async (req, res, next) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];
    
    if (!token) {
      return res.status(401).json({ error: 'No token provided' });
    }
    
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' });
  }
};
"""
    
    def _generate_validation_middleware(self, config: Dict[str, Any]) -> str:
        """Generate validation middleware"""
        
        return """const { validationResult } = require('express-validator');

module.exports = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }
  next();
};
"""
    
    def _generate_error_handler(self, config: Dict[str, Any]) -> str:
        """Generate error handling middleware"""
        
        return """module.exports = (err, req, res, next) => {
  console.error(err.stack);
  
  const status = err.status || 500;
  const message = err.message || 'Internal Server Error';
  
  res.status(status).json({
    error: {
      message,
      status,
      timestamp: new Date().toISOString()
    }
  });
};
"""
    
    def _generate_routes(self, api_design: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate routes file"""
        
        return """const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');

// Import controllers
// const AuthController = require('../controllers/AuthController');

// Auth routes
router.post('/auth/register', /* AuthController.register */);
router.post('/auth/login', /* AuthController.login */);

// Protected routes
router.use(authMiddleware);

module.exports = router;
"""
    
    def _generate_db_config(self, config: Dict[str, Any]) -> str:
        """Generate database configuration"""
        
        if config['database'] == 'postgresql':
            return """const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

async function connectDatabase() {
  try {
    await pool.connect();
    console.log('Database connected');
  } catch (error) {
    console.error('Database connection failed:', error);
    throw error;
  }
}

module.exports = { pool, connectDatabase };
"""
        else:
            return "// Database config"
    
    def _generate_env_config(self, config: Dict[str, Any]) -> str:
        """Generate environment configuration"""
        
        return """require('dotenv').config();

module.exports = {
  port: process.env.PORT || 3000,
  databaseUrl: process.env.DATABASE_URL,
  jwtSecret: process.env.JWT_SECRET,
  nodeEnv: process.env.NODE_ENV || 'development'
};
"""
    
    def _generate_migrations(self, db_schema: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate database migrations"""
        
        migrations = []
        
        for table in db_schema.get('tables', []):
            migration_name = f"create_{table['name']}_table"
            migration_sql = self._generate_migration_sql(table, config)
            
            migrations.append({
                'name': migration_name,
                'sql': migration_sql
            })
        
        return migrations
    
    def _generate_migration_sql(self, table: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate SQL for a table migration"""
        
        columns = []
        for col in table['columns']:
            col_def = f"{col['name']} {col['type']}"
            if not col.get('nullable', True):
                col_def += " NOT NULL"
            if col.get('unique'):
                col_def += " UNIQUE"
            if col.get('default'):
                col_def += f" DEFAULT {col['default']}"
            columns.append(col_def)
        
        return f"""CREATE TABLE {table['name']} (
  {',\n  '.join(columns)}
);
"""
    
    def _generate_api_spec(self, api_design: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 specification"""
        
        return {
            'openapi': '3.0.0',
            'info': {
                'title': 'API',
                'version': '1.0.0'
            },
            'paths': {
                endpoint['path']: {
                    endpoint['method'].lower(): {
                        'summary': endpoint.get('description', ''),
                        'security': [{'bearerAuth': []}] if endpoint.get('auth_required') else []
                    }
                }
                for endpoint in api_design.get('endpoints', [])
            }
        }
    
    def _generate_package_json(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate package.json"""
        
        return {
            'name': 'backend-api',
            'version': '1.0.0',
            'main': 'src/server.js',
            'scripts': {
                'start': 'node src/server.js',
                'dev': 'nodemon src/server.js',
                'migrate': 'prisma migrate dev'
            },
            'dependencies': {
                'express': '^4.18.0',
                'cors': '^2.8.5',
                'helmet': '^7.0.0',
                'express-rate-limit': '^6.0.0',
                'jsonwebtoken': '^9.0.0',
                'bcrypt': '^5.1.0',
                'dotenv': '^16.0.0',
                'pg': '^8.11.0' if config['database'] == 'postgresql' else None
            }
        }
    
    def _generate_env_example(self, config: Dict[str, Any]) -> str:
        """Generate .env.example file"""
        
        return """PORT=3000
NODE_ENV=development
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
JWT_SECRET=your-secret-key-here
"""
    
    def _generate_setup_instructions(self, config: Dict[str, Any]) -> str:
        """Generate setup instructions"""
        
        return f"""# Backend Setup

## Installation
```bash
npm install
```

## Database Setup
```bash
# Run migrations
npm run migrate
```

## Development
```bash
npm run dev
```

## Configuration
- Backend: {config['backend']}
- Framework: {config['framework']}
- Database: {config['database']}
"""
    
    def _generate_readme(self, config: Dict[str, Any]) -> str:
        """Generate README"""
        
        return f"""# Backend API

Built with {config['framework'].title()} and {config['database'].title()}.

## Quick Start

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run migrations:
   ```bash
   npm run migrate
   ```

4. Start server:
   ```bash
   npm run dev
   ```

## API Documentation

See `/api/docs` for interactive API documentation.
"""
    
    def _clean_code(self, code: str) -> str:
        """Clean code from LLM response"""
        if '```' in code:
            code = code.split('```')[1]
            if code.startswith(('javascript', 'js', 'python', 'py')):
                code = '\n'.join(code.split('\n')[1:])
        return code.strip()
    
    def _calculate_backend_confidence(
        self,
        code_files: Dict[str, str],
        api_design: Dict[str, Any],
        db_schema: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> float:
        """Calculate confidence in generated backend"""
        
        criteria = {
            'has_server_file': 'src/server.js' in code_files or 'src/main.py' in code_files,
            'has_routes': any('route' in f.lower() for f in code_files.keys()),
            'has_controllers': any('controller' in f.lower() for f in code_files.keys()),
            'has_models': any('model' in f.lower() for f in code_files.keys()),
            'has_middleware': any('middleware' in f.lower() for f in code_files.keys()),
            'has_db_config': any('database' in f.lower() for f in code_files.keys()),
            'has_package_json': 'package.json' in code_files,
            'has_env_example': '.env.example' in code_files,
            'has_endpoints': len(api_design.get('endpoints', [])) >= 3,
            'has_database_tables': len(db_schema.get('tables', [])) >= 1
        }
        
        weights = {
            'has_server_file': 2.0,
            'has_routes': 1.5,
            'has_controllers': 1.5,
            'has_models': 1.5,
            'has_middleware': 1.0,
            'has_db_config': 1.0,
            'has_package_json': 1.0,
            'has_env_example': 0.5,
            'has_endpoints': 2.0,
            'has_database_tables': 1.5
        }
        
        return self._calculate_confidence(criteria, weights)


if __name__ == '__main__':
    from antigravity.llm.kimi_adapter import KimiAdapter
    
    adapter = KimiAdapter(api_key="MOCK_KEY")
    agent = BackendEngineerAgent(llm_adapter=adapter)
    
    test_requirements = {
        'product_name': 'Task Manager',
        'features': [
            {'name': 'User authentication', 'priority': 'high'},
            {'name': 'Task CRUD', 'priority': 'high'}
        ]
    }
    
    result = agent.execute_with_retry({
        'requirements': test_requirements,
        'config': {'backend': 'nodejs', 'database': 'postgresql'}
    })
    
    print(f"\nSuccess: {result.success}")
    print(f"Confidence: {result.confidence}%")
    print(f"Files: {len(result.outputs.get('code_files', {}))}")
