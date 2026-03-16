"""
Frontend Engineer Agent

Generates complete frontend applications from product requirements.
Supports React, Next.js, and Vue with modern best practices.
"""

import json
from typing import Dict, List, Any, Tuple, Optional
from agents.base_agent import BaseAgent, AgentType, AgentResult


class FrontendEngineerAgent(BaseAgent):
    """
    Agent responsible for generating frontend code.
    
    Inputs:
        - requirements: Product requirements (from Product Interpreter)
        - config: Frontend configuration (framework, styling, etc.)
    
    Outputs:
        - code_files: Dict of filename -> code content
        - component_list: List of components created
        - routing_config: Routing configuration
        - dependencies: Package.json dependencies
        - setup_instructions: How to run the app
    """
    
    def __init__(self, llm_adapter: Any, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            agent_type=AgentType.FRONTEND_ENGINEER,
            llm_adapter=llm_adapter,
            config=config
        )
        
        # Default frontend config
        self.default_config = {
            'framework': 'react',  # react, nextjs, vue
            'styling': 'tailwind',  # tailwind, css-modules, styled-components
            'state_management': 'zustand',  # zustand, redux, context
            'typescript': True,
            'accessibility': True,
            'responsive': True
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
            elif 'features' not in req or 'pages' not in req:
                errors.append("Requirements must include 'features' and 'pages'")
        
        return len(errors) == 0, errors
    
    def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute frontend code generation
        
        Args:
            inputs: Dict with 'requirements' and optional 'config'
        
        Returns:
            AgentResult with generated frontend code
        """
        self.logger.info("Starting frontend code generation")
        
        requirements = inputs['requirements']
        config = {**self.default_config, **inputs.get('config', {})}
        
        # Step 1: Design component architecture
        self.logger.info("Designing component architecture")
        component_architecture = self._design_components(requirements, config)
        
        # Step 2: Generate code files
        self.logger.info("Generating code files")
        code_files = self._generate_code_files(
            requirements,
            component_architecture,
            config
        )
        
        # Step 3: Generate package.json
        dependencies = self._generate_dependencies(config)
        
        # Step 4: Generate setup instructions
        setup_instructions = self._generate_setup_instructions(config)
        
        # Calculate confidence
        confidence = self._calculate_frontend_confidence(
            code_files,
            component_architecture,
            requirements
        )
        
        # Log decision
        self.log_decision(
            decision=f"Generated {config['framework']} frontend with {len(code_files)} files",
            reasoning=f"Created {len(component_architecture['components'])} components, "
                     f"using {config['styling']} for styling, "
                     f"confidence: {confidence}%"
        )
        
        return AgentResult(
            success=True,
            confidence=confidence,
            outputs={
                'code_files': code_files,
                'component_architecture': component_architecture,
                'dependencies': dependencies,
                'setup_instructions': setup_instructions,
                'config': config
            },
            metadata={
                'framework': config['framework'],
                'file_count': len(code_files),
                'component_count': len(component_architecture['components'])
            }
        )
    
    def _design_components(
        self,
        requirements: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Design component architecture using LLM
        
        Returns:
            Component architecture specification
        """
        prompt = f"""
You are a Senior Frontend Engineer. Design a component architecture for the following application.

Requirements:
{json.dumps(requirements, indent=2)}

Framework: {config['framework']}
Styling: {config['styling']}
State Management: {config['state_management']}

Create a component architecture in JSON format:

{{
  "components": [
    {{
      "name": "string",
      "type": "page|layout|feature|common",
      "path": "string (file path)",
      "props": ["string"],
      "state": ["string"],
      "children": ["string (component names)"]
    }}
  ],
  "routing": [
    {{
      "path": "string (URL path)",
      "component": "string (component name)",
      "protected": boolean
    }}
  ],
  "state_structure": {{
    "stores": ["string"],
    "global_state": ["string"]
  }}
}}

Return ONLY the JSON, no additional text.
"""
        
        response = self._call_llm(prompt, temperature=0.5)
        architecture = self._parse_json_from_llm(response)
        
        if not architecture:
            # Fallback to basic architecture
            self.logger.warning("Failed to parse architecture, using fallback")
            architecture = self._create_fallback_architecture(requirements)
        
        return architecture
    
    def _create_fallback_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create a basic fallback architecture"""
        components = []
        routing = []
        
        # Create components for each page
        for page in requirements.get('pages', []):
            components.append({
                'name': page['name'].replace(' ', ''),
                'type': 'page',
                'path': f"src/pages/{page['name'].replace(' ', '')}.jsx",
                'props': [],
                'state': [],
                'children': []
            })
            
            routing.append({
                'path': page.get('route', f"/{page['name'].lower().replace(' ', '-')}"),
                'component': page['name'].replace(' ', ''),
                'protected': False
            })
        
        return {
            'components': components,
            'routing': routing,
            'state_structure': {
                'stores': ['authStore', 'appStore'],
                'global_state': ['user', 'theme']
            }
        }
    
    def _generate_code_files(
        self,
        requirements: Dict[str, Any],
        architecture: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate all code files
        
        Returns:
            Dict of filename -> code content
        """
        code_files = {}
        
        # Generate each component
        for component in architecture['components']:
            self.logger.info(f"Generating component: {component['name']}")
            code = self._generate_component_code(component, config)
            code_files[component['path']] = code
        
        # Generate App.jsx / main entry point
        code_files['src/App.jsx'] = self._generate_app_file(architecture, config)
        
        # Generate routing configuration
        if config['framework'] == 'react':
            code_files['src/routes.jsx'] = self._generate_routes_file(architecture)
        
        # Generate state management
        code_files['src/store/index.js'] = self._generate_store_file(architecture, config)
        
        # Generate styles
        if config['styling'] == 'tailwind':
            code_files['src/index.css'] = self._generate_tailwind_css()
        
        # Generate package.json
        code_files['package.json'] = json.dumps(
            self._generate_dependencies(config),
            indent=2
        )
        
        # Generate README
        code_files['README.md'] = self._generate_readme(config)
        
        return code_files
    
    def _generate_component_code(
        self,
        component: Dict[str, Any],
        config: Dict[str, Any]
    ) -> str:
        """Generate code for a single component"""
        
        # Use LLM to generate component code
        prompt = f"""
Generate a {config['framework']} component with the following specification:

Component Name: {component['name']}
Type: {component['type']}
Props: {component.get('props', [])}
State: {component.get('state', [])}
Children: {component.get('children', [])}

Requirements:
- Use {config['styling']} for styling
- {'Use TypeScript' if config['typescript'] else 'Use JavaScript'}
- {'Include ARIA labels and semantic HTML' if config['accessibility'] else ''}
- {'Make it responsive (mobile-first)' if config['responsive'] else ''}
- Use modern React hooks
- Include error boundaries where appropriate
- Add loading states

Return ONLY the component code, no explanations.
"""
        
        code = self._call_llm(prompt, temperature=0.3, max_tokens=2048)
        
        # Clean up code (remove markdown code blocks if present)
        if '```' in code:
            code = code.split('```')[1]
            if code.startswith('jsx') or code.startswith('javascript') or code.startswith('typescript'):
                code = '\n'.join(code.split('\n')[1:])
        
        return code.strip()
    
    def _generate_app_file(self, architecture: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate main App file"""
        if config['framework'] == 'react':
            return """import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import Routes from './routes';
import './index.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes />
      </div>
    </Router>
  );
}

export default App;
"""
        elif config['framework'] == 'nextjs':
            return """import type { AppProps } from 'next/app';
import '../styles/globals.css';

function MyApp({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}

export default MyApp;
"""
        else:  # Vue
            return """import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import './index.css';

createApp(App)
  .use(router)
  .mount('#app');
"""
    
    def _generate_routes_file(self, architecture: Dict[str, Any]) -> str:
        """Generate routing configuration"""
        routes = architecture.get('routing', [])
        
        imports = []
        route_configs = []
        
        for route in routes:
            component_name = route['component']
            imports.append(f"import {component_name} from './pages/{component_name}';")
            
            protected = ', protected: true' if route.get('protected') else ''
            route_configs.append(f"  {{ path: '{route['path']}', component: {component_name}{protected} }}")
        
        return f"""import React from 'react';
import {{ Routes, Route }} from 'react-router-dom';
{chr(10).join(imports)}

const routes = [
{chr(10).join(route_configs)}
];

export default function AppRoutes() {{
  return (
    <Routes>
      {{routes.map((route, index) => (
        <Route key={{index}} path={{route.path}} element={{<route.component />}} />
      ))}}
    </Routes>
  );
}}
"""
    
    def _generate_store_file(self, architecture: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate state management configuration"""
        if config['state_management'] == 'zustand':
            return """import { create } from 'zustand';

export const useStore = create((set) => ({
  user: null,
  theme: 'light',
  setUser: (user) => set({ user }),
  setTheme: (theme) => set({ theme }),
}));
"""
        elif config['state_management'] == 'redux':
            return """import { configureStore } from '@reduxjs/toolkit';

export const store = configureStore({
  reducer: {
    // Add reducers here
  },
});
"""
        else:  # Context API
            return """import React, { createContext, useContext, useState } from 'react';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [state, setState] = useState({
    user: null,
    theme: 'light',
  });

  return (
    <AppContext.Provider value={{ state, setState }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => useContext(AppContext);
"""
    
    def _generate_tailwind_css(self) -> str:
        """Generate Tailwind CSS configuration"""
        return """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
  }
  
  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
  }
}

@layer components {
  .btn-primary {
    @apply bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors;
  }
}
"""
    
    def _generate_dependencies(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate package.json dependencies"""
        base_deps = {
            "name": "frontend-app",
            "version": "1.0.0",
            "private": True,
            "dependencies": {}
        }
        
        if config['framework'] == 'react':
            base_deps['dependencies'].update({
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.20.0"
            })
        elif config['framework'] == 'nextjs':
            base_deps['dependencies'].update({
                "next": "^14.0.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            })
        
        if config['styling'] == 'tailwind':
            base_deps['dependencies']['tailwindcss'] = "^3.3.0"
        
        if config['state_management'] == 'zustand':
            base_deps['dependencies']['zustand'] = "^4.4.0"
        elif config['state_management'] == 'redux':
            base_deps['dependencies']['@reduxjs/toolkit'] = "^2.0.0"
            base_deps['dependencies']['react-redux'] = "^9.0.0"
        
        base_deps['scripts'] = {
            "dev": "vite" if config['framework'] == 'react' else "next dev",
            "build": "vite build" if config['framework'] == 'react' else "next build",
            "start": "vite preview" if config['framework'] == 'react' else "next start"
        }
        
        return base_deps
    
    def _generate_setup_instructions(self, config: Dict[str, Any]) -> str:
        """Generate setup instructions"""
        return f"""# Frontend Setup Instructions

## Installation
```bash
npm install
```

## Development
```bash
npm run dev
```

## Build
```bash
npm run build
```

## Configuration
- Framework: {config['framework']}
- Styling: {config['styling']}
- State Management: {config['state_management']}
- TypeScript: {'Yes' if config['typescript'] else 'No'}

## Environment Variables
Create a `.env.local` file with:
```
VITE_API_URL=http://localhost:3000/api
```
"""
    
    def _generate_readme(self, config: Dict[str, Any]) -> str:
        """Generate README file"""
        return f"""# Frontend Application

Built with {config['framework'].title()}, {config['styling'].title()}, and {config['state_management'].title()}.

## Quick Start

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run development server:
   ```bash
   npm run dev
   ```

3. Open http://localhost:3000

## Tech Stack

- **Framework**: {config['framework'].title()}
- **Styling**: {config['styling'].title()}
- **State Management**: {config['state_management'].title()}
- **TypeScript**: {'Yes' if config['typescript'] else 'No'}

## Project Structure

```
src/
├── components/     # Reusable components
├── pages/          # Page components
├── store/          # State management
├── utils/          # Utility functions
└── App.jsx         # Main app component
```
"""
    
    def _calculate_frontend_confidence(
        self,
        code_files: Dict[str, str],
        architecture: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> float:
        """Calculate confidence in generated frontend"""
        
        criteria = {
            'has_app_file': 'src/App.jsx' in code_files or 'src/App.tsx' in code_files,
            'has_routing': any('route' in f.lower() for f in code_files.keys()),
            'has_state_management': any('store' in f.lower() for f in code_files.keys()),
            'has_styles': any('.css' in f for f in code_files.keys()),
            'has_package_json': 'package.json' in code_files,
            'has_readme': 'README.md' in code_files,
            'components_match_pages': len(architecture.get('components', [])) >= len(requirements.get('pages', [])),
            'has_multiple_files': len(code_files) >= 5
        }
        
        weights = {
            'has_app_file': 2.0,
            'has_routing': 1.5,
            'has_state_management': 1.5,
            'has_styles': 1.0,
            'has_package_json': 1.0,
            'has_readme': 0.5,
            'components_match_pages': 2.0,
            'has_multiple_files': 1.0
        }
        
        return self._calculate_confidence(criteria, weights)


if __name__ == '__main__':
    # Test the agent
    from antigravity.llm.kimi_adapter import KimiAdapter
    
    adapter = KimiAdapter(api_key="MOCK_KEY")
    agent = FrontendEngineerAgent(llm_adapter=adapter)
    
    # Test input
    test_requirements = {
        'product_name': 'Task Manager',
        'features': [
            {'name': 'Create tasks', 'priority': 'high'},
            {'name': 'Assign tasks', 'priority': 'high'}
        ],
        'pages': [
            {'name': 'Dashboard', 'route': '/'},
            {'name': 'Tasks', 'route': '/tasks'}
        ]
    }
    
    test_input = {
        'requirements': test_requirements,
        'config': {
            'framework': 'react',
            'styling': 'tailwind'
        }
    }
    
    result = agent.execute_with_retry(test_input)
    
    print(f"\nSuccess: {result.success}")
    print(f"Confidence: {result.confidence}%")
    print(f"Files generated: {len(result.outputs.get('code_files', {}))}")
