import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { ReadableAnswer } from './ReadableAnswer';

it('renders common answer formatting as readable text', () => {
  render(<ReadableAnswer text={'**Conclusão** com `fonte`.\n\n- Primeiro dado\n- Segundo dado'}/>);
  expect(screen.getByText('Conclusão').tagName).toBe('STRONG');
  expect(screen.getByText('fonte').tagName).toBe('CODE');
  expect(screen.getAllByRole('listitem')).toHaveLength(2);
});
