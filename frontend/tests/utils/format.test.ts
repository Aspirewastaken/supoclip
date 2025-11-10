import { describe, it, expect } from 'vitest';

/**
 * Example utility function tests
 * Replace these with actual utility functions from your codebase
 */

describe('Time formatting utilities', () => {
  const formatTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    }
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  it('formats seconds correctly', () => {
    expect(formatTime(30)).toBe('30s');
    expect(formatTime(45)).toBe('45s');
  });

  it('formats minutes and seconds correctly', () => {
    expect(formatTime(90)).toBe('1m 30s');
    expect(formatTime(120)).toBe('2m 0s');
    expect(formatTime(185)).toBe('3m 5s');
  });

  it('handles zero', () => {
    expect(formatTime(0)).toBe('0s');
  });

  it('rounds partial seconds', () => {
    expect(formatTime(30.7)).toBe('31s');
    expect(formatTime(90.3)).toBe('1m 30s');
  });
});

describe('Timestamp parsing utilities', () => {
  const parseTimestamp = (timestamp: string): number => {
    const parts = timestamp.split(':');
    if (parts.length !== 2) {
      throw new Error('Invalid timestamp format');
    }
    const minutes = parseInt(parts[0], 10);
    const seconds = parseInt(parts[1], 10);
    return minutes * 60 + seconds;
  };

  it('parses MM:SS format correctly', () => {
    expect(parseTimestamp('0:30')).toBe(30);
    expect(parseTimestamp('1:30')).toBe(90);
    expect(parseTimestamp('10:45')).toBe(645);
  });

  it('handles zero padding', () => {
    expect(parseTimestamp('0:05')).toBe(5);
    expect(parseTimestamp('1:00')).toBe(60);
  });

  it('throws on invalid format', () => {
    expect(() => parseTimestamp('invalid')).toThrow();
    expect(() => parseTimestamp('1:2:3')).toThrow();
  });
});

describe('File size formatting', () => {
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };

  it('formats bytes correctly', () => {
    expect(formatFileSize(500)).toBe('500 B');
  });

  it('formats kilobytes correctly', () => {
    expect(formatFileSize(1536)).toBe('1.5 KB');
    expect(formatFileSize(5120)).toBe('5.0 KB');
  });

  it('formats megabytes correctly', () => {
    expect(formatFileSize(2 * 1024 * 1024)).toBe('2.0 MB');
    expect(formatFileSize(5.5 * 1024 * 1024)).toBe('5.5 MB');
  });

  it('formats gigabytes correctly', () => {
    expect(formatFileSize(2 * 1024 * 1024 * 1024)).toBe('2.0 GB');
  });
});
