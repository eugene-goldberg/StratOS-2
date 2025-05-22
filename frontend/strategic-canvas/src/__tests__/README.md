# Strategic Canvas Test Suite

This directory contains comprehensive tests for the Strategic Canvas React application.

## Test Structure

```
__tests__/
├── components/           # Component unit tests
│   ├── StrategicCanvas.test.tsx
│   ├── CanvasToolbar.test.tsx
│   └── AIAssistPanel.test.tsx
├── store/               # Zustand store tests
│   └── strategicCanvasStore.test.ts
├── services/            # API service tests
│   └── strategicCanvasService.test.ts
├── types/               # TypeScript type tests
│   └── index.test.ts
├── integration/         # End-to-end workflow tests
│   └── workflows.test.tsx
├── test-utils.tsx       # Testing utilities and setup
└── README.md           # This file
```

## Test Categories

### 1. Component Tests
- **StrategicCanvas.test.tsx**: Tests the main canvas component including ReactFlow integration, event handling, and AI panel management
- **CanvasToolbar.test.tsx**: Tests toolbar functionality, node creation, zoom operations, and button states
- **AIAssistPanel.test.tsx**: Tests AI analysis results display, theme chips, suggested connections, and panel interactions

### 2. Store Tests
- **strategicCanvasStore.test.ts**: Tests Zustand store operations including:
  - Node CRUD operations
  - Edge management
  - Selection handling
  - Canvas persistence
  - AI integration
  - Viewport management

### 3. Service Tests
- **strategicCanvasService.test.ts**: Tests API service functions with mocked HTTP requests:
  - Canvas save/load operations
  - AI theme analysis
  - Error handling and fallbacks
  - MSW integration examples

### 4. Type Tests
- **index.test.ts**: TypeScript compile-time and runtime type validation:
  - Node data type validation
  - Enum value checks
  - Type guard functions
  - Interface conformance

### 5. Integration Tests
- **workflows.test.tsx**: End-to-end user workflows:
  - Complete canvas creation and editing
  - SWOT analysis workflow
  - AI analysis and suggestions
  - Error handling scenarios
  - Accessibility compliance

## Testing Libraries Used

- **@testing-library/react**: Component testing utilities
- **@testing-library/jest-dom**: Extended Jest matchers
- **@testing-library/user-event**: User interaction simulation
- **MSW (Mock Service Worker)**: API mocking
- **Jest**: Test runner and assertions

## Mocking Strategy

### ReactFlow Mocking
ReactFlow components and hooks are mocked in `__mocks__/reactflow.ts` to:
- Avoid complex DOM dependencies
- Focus on component logic
- Ensure consistent test behavior

### Store Mocking
Zustand store is mocked for component tests to:
- Isolate component behavior
- Control state precisely
- Test state interactions

### API Mocking
HTTP requests are mocked using MSW to:
- Simulate API responses
- Test error scenarios
- Avoid external dependencies

## Running Tests

```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in CI mode
npm run test:ci

# Run specific test file
npm test CanvasToolbar.test.tsx

# Run tests in watch mode
npm test -- --watch
```

## Coverage Goals

- **Statements**: > 90%
- **Branches**: > 85%
- **Functions**: > 90%
- **Lines**: > 90%

## Test Best Practices

### 1. Component Testing
- Test user interactions, not implementation details
- Use semantic queries (getByRole, getByLabelText)
- Mock external dependencies
- Test error states and edge cases

### 2. Store Testing
- Test state changes and side effects
- Verify async operations
- Test error handling
- Ensure state consistency

### 3. Integration Testing
- Test complete user workflows
- Verify component interactions
- Test accessibility
- Cover happy path and error scenarios

## Continuous Integration

Tests are configured to run in CI/CD pipelines with:
- Coverage reporting
- Performance monitoring
- Accessibility checking
- Cross-browser compatibility

## Debugging Tests

### Common Issues
1. **ReactFlow errors**: Ensure mocks are properly configured
2. **Async timing**: Use `waitFor` for async operations
3. **State persistence**: Reset store state between tests
4. **MSW handlers**: Verify request/response patterns

### Debug Commands
```bash
# Run tests with debugging
npm test -- --verbose

# Run single test with debug info
npm test -- --testNamePattern="should render correctly" --verbose

# Generate coverage report
npm run test:coverage
```

## Contributing

When adding new tests:
1. Follow existing naming conventions
2. Include both happy path and error scenarios
3. Add integration tests for new workflows
4. Update this README if adding new test categories
5. Ensure tests are deterministic and fast

## Future Enhancements

- Visual regression testing
- Performance benchmarking
- E2E tests with Playwright
- Accessibility automation
- Snapshot testing for components