/**
 * File: utils.ts
 * Purpose: Utility function for merging Tailwind CSS classes with conflict resolution.
 *          Combines clsx and tailwind-merge to handle conditional classes and Tailwind conflicts.
 * Author: Hamza Ahmad
 */
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
