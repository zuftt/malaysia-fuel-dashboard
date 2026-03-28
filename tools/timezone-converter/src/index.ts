/**
 * Timezone Converter Library
 * High-performance timezone conversion with scheduling
 */

interface TimeResult {
  timezone: string;
  time: string;
  date: string;
  formatted: string;
  offset: string;
}

interface MeetingSchedule {
  timezone: string;
  localTime: string;
  isConvenient: boolean;
  hourOfDay: number;
}

const TIMEZONE_DATA: Record<string, string> = {
  'kl': 'Asia/Kuala_Lumpur',
  'sg': 'Asia/Singapore',
  'hk': 'Asia/Hong_Kong',
  'jp': 'Asia/Tokyo',
  'ny': 'America/New_York',
  'la': 'America/Los_Angeles',
  'london': 'Europe/London',
  'dubai': 'Asia/Dubai',
  'sydney': 'Australia/Sydney',
  'auckland': 'Pacific/Auckland',
};

export class TimezoneConverter {
  /**
   * Convert time to multiple timezones
   */
  static convert(time: string, fromTz: string, toTzs: string[]): TimeResult[] {
    const date = new Date(time);
    
    return toTzs.map(tz => {
      const resolvedTz = TIMEZONE_DATA[tz.toLowerCase()] || tz;
      
      const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: resolvedTz,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });

      const parts = formatter.formatToParts(date);
      const timeStr = `${parts[8].value}:${parts[10].value}:${parts[12].value}`;
      const dateStr = `${parts[4].value}-${parts[0].value}-${parts[2].value}`;

      return {
        timezone: tz,
        time: timeStr,
        date: dateStr,
        formatted: `${timeStr} on ${dateStr}`,
        offset: this.getOffset(date, resolvedTz),
      };
    });
  }

  /**
   * Find best meeting time across timezones
   * (9 AM - 5 PM is "convenient", 7 AM - 10 PM is "okay", rest is rough)
   */
  static findBestMeetingTime(timezones: string[], startTime: Date = new Date()): MeetingSchedule[] {
    const results: MeetingSchedule[] = [];
    const testTime = new Date(startTime);

    for (let hour = 0; hour < 24; hour++) {
      testTime.setUTCHours(hour, 0, 0, 0);
      let totalScore = 0;

      for (const tz of timezones) {
        const resolved = TIMEZONE_DATA[tz.toLowerCase()] || tz;
        const formatter = new Intl.DateTimeFormat('en-US', {
          timeZone: resolved,
          hour: '2-digit',
          hour12: false,
        });
        const parts = formatter.formatToParts(testTime);
        const localHour = parseInt(parts[0].value, 10);

        if (localHour >= 9 && localHour < 17) totalScore += 10;
        else if (localHour >= 7 && localHour < 22) totalScore += 5;
      }

      if (totalScore / timezones.length > 5) {
        const formatter = new Intl.DateTimeFormat('en-US', {
          timeZone: TIMEZONE_DATA[timezones[0].toLowerCase()] || timezones[0],
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
        });
        const parts = formatter.formatToParts(testTime);
        const localTime = `${parts[0].value}:${parts[2].value}`;

        results.push({
          timezone: timezones[0],
          localTime,
          isConvenient: true,
          hourOfDay: hour,
        });
      }
    }

    return results;
  }

  private static getOffset(date: Date, tz: string): string {
    const formatter = new Intl.DateTimeFormat('en-US', {
      timeZone: tz,
      hour: '2-digit',
      minute: '2-digit',
    });
    // Simplified offset calculation
    return 'UTC±X (see tzdata)';
  }
}

export default TimezoneConverter;
