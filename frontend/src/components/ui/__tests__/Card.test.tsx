import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Card } from '../Card';

describe('Card Component', () => {
  // Test basic rendering
  it('renders card with children', () => {
    render(
      <Card>
        <p>Card content</p>
      </Card>
    );
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  // Test default styling
  it('applies default styling', () => {
    render(
      <Card data-testid="card">
        <p>Content</p>
      </Card>
    );
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('bg-container', 'rounded-lg', 'border', 'border-border');
  });

  // Test default shadow
  it('applies shadow by default', () => {
    render(
      <Card data-testid="card">
        <p>Content</p>
      </Card>
    );
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('shadow-soft');
  });

  // Test shadow disabled
  it('does not apply shadow when disabled', () => {
    render(
      <Card shadow={false} data-testid="card">
        <p>Content</p>
      </Card>
    );
    const card = screen.getByTestId('card');
    expect(card).not.toHaveClass('shadow-soft');
  });

  // Test default padding
  it('applies medium padding by default', () => {
    render(
      <Card data-testid="card">
        <p>Content</p>
      </Card>
    );
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('p-4');
  });

  // Test no padding
  it('applies no padding when specified', () => {
    render(
      <Card padding="none" data-testid="card">
        <p>Content</p>
      </Card>
    );
    const card = screen.getByTestId('card');
    expect(card).not.toHaveClass('p-3', 'p-4', 'p-6');
  });

  // Test small padding
  it('applies small padding when specified', () => {
    render(
      <Card padding="small" data-testid="card">
        <p>Content</p>
      </Card>
    );
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('p-3');
  });

  // Test large padding
  it('applies large padding when specified', () => {
    render(
      <Card padding="large" data-testid="card">
        <p>Content</p>
      </Card>
    );
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('p-6');
  });

  // Test custom className
  it('applies custom className', () => {
    render(
      <Card className="custom-class" data-testid="card">
        <p>Content</p>
      </Card>
    );
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('custom-class');
  });

  // Test complex children content
  it('renders complex children content', () => {
    render(
      <Card>
        <h2>Card Title</h2>
        <p>Card description</p>
        <button>Action Button</button>
      </Card>
    );
    expect(screen.getByText('Card Title')).toBeInTheDocument();
    expect(screen.getByText('Card description')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Action Button' })).toBeInTheDocument();
  });

  // Test nested components
  it('renders nested components correctly', () => {
    render(
      <Card>
        <div>
          <span>Nested content</span>
        </div>
      </Card>
    );
    expect(screen.getByText('Nested content')).toBeInTheDocument();
  });

  // Test multiple cards
  it('renders multiple cards independently', () => {
    render(
      <div>
        <Card data-testid="card1">
          <p>First card</p>
        </Card>
        <Card data-testid="card2" padding="large">
          <p>Second card</p>
        </Card>
      </div>
    );
    const card1 = screen.getByTestId('card1');
    const card2 = screen.getByTestId('card2');
    
    expect(card1).toHaveClass('p-4');
    expect(card2).toHaveClass('p-6');
    expect(screen.getByText('First card')).toBeInTheDocument();
    expect(screen.getByText('Second card')).toBeInTheDocument();
  });

  // Test all padding variants
  it('applies correct padding for all variants', () => {
    const { rerender } = render(
      <Card padding="none" data-testid="card">
        <p>Content</p>
      </Card>
    );
    let card = screen.getByTestId('card');
    expect(card).not.toHaveClass('p-3', 'p-4', 'p-6');

    rerender(
      <Card padding="small" data-testid="card">
        <p>Content</p>
      </Card>
    );
    card = screen.getByTestId('card');
    expect(card).toHaveClass('p-3');

    rerender(
      <Card padding="medium" data-testid="card">
        <p>Content</p>
      </Card>
    );
    card = screen.getByTestId('card');
    expect(card).toHaveClass('p-4');

    rerender(
      <Card padding="large" data-testid="card">
        <p>Content</p>
      </Card>
    );
    card = screen.getByTestId('card');
    expect(card).toHaveClass('p-6');
  });

  // Test className combination
  it('combines custom className with default classes', () => {
    render(
      <Card className="my-custom-class another-class" data-testid="card">
        <p>Content</p>
      </Card>
    );
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('bg-container', 'rounded-lg', 'my-custom-class', 'another-class');
  });

  // Test empty children
  it('renders with empty children', () => {
    render(<Card data-testid="card">{null}</Card>);
    const card = screen.getByTestId('card');
    expect(card).toBeInTheDocument();
    expect(card).toBeEmptyDOMElement();
  });
});
