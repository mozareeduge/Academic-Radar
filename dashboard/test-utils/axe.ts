import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

export async function checkAxeViolations(element: HTMLElement) {
  const results = await axe(element);
  expect(results).toHaveNoViolations();
  return results;
}

export async function checkColorOnlyViolations(element: HTMLElement) {
  const statusChips = element.querySelectorAll('[class*="status"], [class*="chip"], [class*="badge"], [role="status"]');
  const violations: string[] = [];

  statusChips.forEach((chip) => {
    const text = chip.textContent?.trim();
    if (!text) {
      violations.push(`Status element has no text: ${chip.outerHTML.substring(0, 100)}`);
    }
  });

  return violations;
}

export async function checkFixedWidths(element: HTMLElement) {
  const violations: string[] = [];
  const allElements = element.querySelectorAll('*');

  allElements.forEach((el) => {
    const style = (el as HTMLElement).getAttribute('style') || '';
    if (style.includes('width') && style.match(/width\s*:\s*[0-9]+px/)) {
      const widthMatch = style.match(/width\s*:\s*([0-9]+)px/);
      if (widthMatch) {
        const width = parseInt(widthMatch[1], 10);
        if (width > 320) {
          violations.push(
            `Element has fixed width > 320px: ${width}px - ${(el as HTMLElement).tagName}`,
          );
        }
      }
    }
  });

  return violations;
}
