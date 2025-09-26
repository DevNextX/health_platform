/**
 * Date/time helpers to normalize server timestamps to the browser's timezone.
 */
import dayjs from 'dayjs';

const TZ_PATTERN = /([zZ]|[+-]\d\d:?\d\d)$/;

const normalizeIsoString = (value) => {
  if (!value) {
    return value;
  }
  let normalized = value.trim();
  if (!normalized.includes('T') && normalized.includes(' ')) {
    normalized = normalized.replace(' ', 'T');
  }
  if (!TZ_PATTERN.test(normalized)) {
    normalized = `${normalized.replace(/Z$/i, '')}Z`;
  }
  return normalized;
};

export const parseServerTime = (value) => {
  if (!value) {
    return dayjs.invalid();
  }
  if (typeof value === 'string' && TZ_PATTERN.test(value)) {
    return dayjs.utc(value).local();
  }
  if (typeof value === 'string') {
    return dayjs.utc(normalizeIsoString(value)).local();
  }
  return dayjs(value);
};

export const formatServerTime = (value, format = 'YYYY-MM-DD HH:mm') => {
  const parsed = parseServerTime(value);
  return parsed.isValid() ? parsed.format(format) : '';
};
