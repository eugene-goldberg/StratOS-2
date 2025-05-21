# Strategic Canvas

A React-based strategic planning canvas application built with React Flow, TypeScript, and Material-UI.

## Features

- Interactive canvas for strategic planning
- Multiple node types (Basic, CEO Log, Data Snippet, SWOT analysis, Risk/Opportunity)
- AI-powered analysis and suggestions
- Real-time collaboration capabilities
- Save/load canvas functionality
- Responsive design with Material-UI

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd strategic-canvas
```

2. Install dependencies:
```bash
npm install
```

### Development

Start the development server:
```bash
npm start
```

The application will open at `http://localhost:3000`.

### Building for Production

Create a production build:
```bash
npm run build
```

Serve the production build:
```bash
npx serve -s build -l 3006
```

## Project Structure

```
src/
├── components/         # React components
│   ├── StrategicCanvas.tsx    # Main canvas component
│   ├── CanvasToolbar.tsx      # Toolbar component
│   ├── AIAssistPanel.tsx      # AI analysis panel
│   └── nodes/                 # Custom node components
├── store/             # Zustand store
├── services/          # API services
├── types/             # TypeScript type definitions
└── utils/             # Utility functions
```

## Technologies Used

- **React** - UI framework
- **TypeScript** - Type safety
- **React Flow** - Interactive diagrams and flows
- **Material-UI** - UI components and styling
- **Zustand** - State management
- **Axios** - HTTP client

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
