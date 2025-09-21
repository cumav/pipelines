# German Insurance Knowledge Selector Pipeline

This pipeline intelligently selects the most relevant German insurance knowledge base (Sparte) based on user queries and integrates with OpenWebUI's knowledge API to provide contextual responses.

## Features

- **Intelligent Knowledge Base Selection**: Analyzes German insurance queries to determine the most relevant insurance type
- **Multi-layered Analysis**: Uses both keyword matching and AI-based analysis for accurate classification
- **OpenWebUI Integration**: Connects to OpenWebUI knowledge bases via API
- **German Insurance Support**: Covers all major German insurance types (Sparten)

## Supported Insurance Types (Sparten)

| Key | Description | German Name |
|-----|-------------|-------------|
| `kfz` | Auto Insurance | Kraftfahrzeugversicherung |
| `kranken` | Health Insurance | Krankenversicherung |
| `haftpflicht` | Liability Insurance | Haftpflichtversicherung |
| `hausrat` | Household Insurance | Hausratversicherung |
| `wohngebäude` | Building Insurance | Wohngebäudeversicherung |
| `leben` | Life Insurance | Lebensversicherung |
| `unfall` | Accident Insurance | Unfallversicherung |
| `rechtsschutz` | Legal Protection Insurance | Rechtsschutzversicherung |
| `reise` | Travel Insurance | Reiseversicherung |
| `berufsunfähigkeit` | Disability Insurance | Berufsunfähigkeitsversicherung |

## Configuration

Configure the pipeline through the valves (settings):

### OpenWebUI Settings
- `OPENWEBUI_BASE_URL`: Base URL of your OpenWebUI instance (default: `http://localhost:3000`)
- `OPENWEBUI_API_KEY`: API key for OpenWebUI authentication (if required)

### AI Analysis Settings  
- `SELECTION_MODEL`: AI model for knowledge base selection (default: `gpt-3.5-turbo`)
- `OPENAI_API_KEY`: OpenAI API key for intelligent analysis (optional - uses keyword matching if not provided)

### Knowledge Base Settings
- `INSURANCE_KNOWLEDGE_BASES`: Mapping of insurance types to descriptions
- `DEFAULT_KNOWLEDGE_BASE`: Fallback knowledge base when no specific match is found

## How It Works

1. **Query Analysis**: The pipeline analyzes the user's German insurance question
2. **Knowledge Base Selection**: 
   - First tries keyword-based matching for common terms
   - Falls back to AI analysis for more complex queries
3. **API Integration**: Queries the selected knowledge base in OpenWebUI
4. **Response Formation**: Returns contextual information specific to the identified insurance type

## Example Queries

```
"Ich hatte einen Autounfall, was zahlt meine KFZ-Versicherung?"
→ Selects: kfz (Auto Insurance)

"Meine Wohnung wurde eingebrochen, welche Versicherung hilft?"
→ Selects: hausrat (Household Insurance)

"Was passiert wenn ich berufsunfähig werde?"
→ Selects: berufsunfähigkeit (Disability Insurance)
```

## Installation

1. Copy the pipeline file to your OpenWebUI pipelines directory
2. Configure the valves with your OpenWebUI instance details
3. Ensure your OpenWebUI instance has knowledge bases named according to the insurance types (kfz, kranken, hausrat, etc.)

## API Endpoints Tested

The pipeline tries multiple possible OpenWebUI API endpoints:
- `/api/v1/knowledge/{knowledge_base}/query`
- `/api/v1/knowledge/query/{knowledge_base}`
- `/api/knowledge/{knowledge_base}/search`
- `/api/v1/documents/search`
- `/api/v1/chat/knowledge/{knowledge_base}`

## Requirements

- `requests`: For API communication
- `openai`: For AI-based query analysis (optional)
- `pydantic`: For configuration management

## Use Cases

- **German Insurance Companies**: Automatically route customer queries to the right department/knowledge base
- **Insurance Brokers**: Quickly access relevant information for different insurance types
- **Customer Service**: Provide accurate, context-specific responses
- **Self-Service Portals**: Enable customers to get answers from the right knowledge source

## Technical Details

- **Keyword Matching**: Fast, rule-based classification for common terms
- **AI Fallback**: Uses OpenAI API for complex or ambiguous queries
- **Error Handling**: Graceful degradation when services are unavailable
- **Flexible API**: Supports multiple OpenWebUI API endpoint formats