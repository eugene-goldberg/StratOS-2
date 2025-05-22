import React from 'react';
import { render, screen } from '../../test-utils';
import userEvent from '@testing-library/user-event';
import AIAssistPanel from '../../components/AIAssistPanel';
import { AIAnalysisResult } from '../../types';

describe('AIAssistPanel', () => {
  const mockOnClose = jest.fn();

  const mockResult: AIAnalysisResult = {
    themes: ['Strategy', 'Innovation', 'Leadership'],
    summary: 'The selected content focuses on strategic leadership and innovation initiatives.',
    suggestedConnections: [
      {
        sourceNodeId: 'node-1',
        targetNodeId: 'node-2',
        label: 'Strategic alignment',
      },
      {
        sourceNodeId: 'node-2',
        targetNodeId: 'node-3',
        label: 'Implementation path',
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders AI analysis results correctly', () => {
    render(<AIAssistPanel result={mockResult} onClose={mockOnClose} />);

    // Check header
    expect(screen.getByText('AI Analysis Results')).toBeInTheDocument();

    // Check themes section
    expect(screen.getByText('Identified Themes')).toBeInTheDocument();
    expect(screen.getByText('Strategy')).toBeInTheDocument();
    expect(screen.getByText('Innovation')).toBeInTheDocument();
    expect(screen.getByText('Leadership')).toBeInTheDocument();

    // Check summary section
    expect(screen.getByText('Summary')).toBeInTheDocument();
    expect(screen.getByText(mockResult.summary)).toBeInTheDocument();

    // Check connections section
    expect(screen.getByText('Suggested Connections')).toBeInTheDocument();
    expect(screen.getByText('Strategic alignment')).toBeInTheDocument();
    expect(screen.getByText('Implementation path')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    
    render(<AIAssistPanel result={mockResult} onClose={mockOnClose} />);

    const closeButton = screen.getByLabelText(/close/i);
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('renders themes as chips', () => {
    render(<AIAssistPanel result={mockResult} onClose={mockOnClose} />);

    // Themes should be rendered as MUI chips
    const strategyChip = screen.getByText('Strategy');
    const innovationChip = screen.getByText('Innovation');
    const leadershipChip = screen.getByText('Leadership');

    expect(strategyChip.closest('.MuiChip-root')).toBeInTheDocument();
    expect(innovationChip.closest('.MuiChip-root')).toBeInTheDocument();
    expect(leadershipChip.closest('.MuiChip-root')).toBeInTheDocument();
  });

  it('handles result with no suggested connections', () => {
    const resultNoConnections: AIAnalysisResult = {
      themes: ['Strategy'],
      summary: 'Basic analysis.',
      suggestedConnections: [],
    };

    render(<AIAssistPanel result={resultNoConnections} onClose={mockOnClose} />);

    // Should not show connections section
    expect(screen.queryByText('Suggested Connections')).not.toBeInTheDocument();
    expect(screen.queryByText('Dotted blue lines have been added')).not.toBeInTheDocument();
  });

  it('handles result with undefined suggested connections', () => {
    const resultUndefinedConnections: AIAnalysisResult = {
      themes: ['Strategy'],
      summary: 'Basic analysis.',
    };

    render(<AIAssistPanel result={resultUndefinedConnections} onClose={mockOnClose} />);

    // Should not show connections section
    expect(screen.queryByText('Suggested Connections')).not.toBeInTheDocument();
  });

  it('displays default label for connections without labels', () => {
    const resultNoLabels: AIAnalysisResult = {
      themes: ['Strategy'],
      summary: 'Analysis with unlabeled connections.',
      suggestedConnections: [
        {
          sourceNodeId: 'node-1',
          targetNodeId: 'node-2',
        },
      ],
    };

    render(<AIAssistPanel result={resultNoLabels} onClose={mockOnClose} />);

    expect(screen.getByText('Related concepts')).toBeInTheDocument();
  });

  it('handles empty themes array', () => {
    const resultEmptyThemes: AIAnalysisResult = {
      themes: [],
      summary: 'Analysis with no themes.',
      suggestedConnections: [],
    };

    render(<AIAssistPanel result={resultEmptyThemes} onClose={mockOnClose} />);

    // Themes section should still be present but empty
    expect(screen.getByText('Identified Themes')).toBeInTheDocument();
    expect(screen.getByText('Analysis with no themes.')).toBeInTheDocument();
  });

  it('displays helper text for suggested connections', () => {
    render(<AIAssistPanel result={mockResult} onClose={mockOnClose} />);

    expect(screen.getByText('Dotted blue lines have been added to your canvas')).toBeInTheDocument();
  });

  it('renders connections in styled boxes', () => {
    render(<AIAssistPanel result={mockResult} onClose={mockOnClose} />);

    const connection1 = screen.getByText('Strategic alignment');
    const connection2 = screen.getByText('Implementation path');

    // Both should be in styled containers
    expect(connection1.closest('.MuiBox-root')).toBeInTheDocument();
    expect(connection2.closest('.MuiBox-root')).toBeInTheDocument();
  });
});