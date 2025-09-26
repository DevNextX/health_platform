/**
 * Date/time helpers to normalize server timestamps to the browser's timezone.
 */
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';

if (typeof dayjs.utc !== 'function') {
  dayjs.extend(utc);
}
if (typeof dayjs.tz !== 'function') {
  dayjs.extend(timezone);
}

const LOCAL_TZ = dayjs.tz?.guess ? dayjs.tz.guess() : undefined;

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
  if (dayjs.isDayjs?.(value)) {
    return value;
  }
  if (value instanceof Date) {
    return dayjs(value);
  }
  if (typeof value === 'string') {
    const normalized = TZ_PATTERN.test(value) ? value : normalizeIsoString(value);
    const utc = dayjs.utc(normalized);
    return LOCAL_TZ ? utc.tz(LOCAL_TZ) : utc.local();
  }
  return dayjs(value);
};

export const formatServerTime = (value, format = 'YYYY-MM-DD HH:mm') => {
  const parsed = parseServerTime(value);
  return parsed.isValid() ? parsed.format(format) : '';
};

export const toServerISOString = (value) => {
  if (!value) {
    return null;
  }
  const parsed = dayjs(value);
  return parsed.isValid() ? parsed.utc().format() : null;
};
