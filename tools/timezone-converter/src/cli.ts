#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import TimezoneConverter from './index';

const program = new Command();

program
  .name('tzc')
  .description('⏰ Lightning-fast timezone converter + meeting scheduler')
  .version('1.0.0');

program
  .command('convert <time>')
  .description('Convert time to multiple timezones')
  .option('-f, --from <tz>', 'From timezone (default: kl)', 'kl')
  .option('-t, --to <tzs>', 'To timezones (comma-separated: ny,london,tokyo)', 'ny,london,sg')
  .action((time, options) => {
    const toTzs = options.to.split(',').map((t: string) => t.trim());
    const results = TimezoneConverter.convert(time || new Date().toISOString(), options.from, toTzs);

    console.log(`\n${chalk.bold.cyan('⏰ Timezone Conversion')}`);
    console.log(chalk.gray('─'.repeat(50)));
    
    results.forEach(r => {
      console.log(`${chalk.green(r.timezone.toUpperCase().padEnd(8))} ${chalk.yellow(r.formatted)}`);
    });
    console.log(chalk.gray('─'.repeat(50)) + '\n');
  });

program
  .command('meeting')
  .description('Find best meeting time across timezones')
  .option('-tz, --timezones <tzs>', 'Timezones to check (comma-separated)', 'kl,ny,london,tokyo')
  .action((options) => {
    const tzs = options.timezones.split(',').map((t: string) => t.trim());
    const schedule = TimezoneConverter.findBestMeetingTime(tzs);

    console.log(`\n${chalk.bold.cyan('📅 Meeting Scheduler')}`);
    console.log(chalk.gray(`Best times across ${tzs.join(', ')}`));
    console.log(chalk.gray('─'.repeat(50)));
    
    if (schedule.length > 0) {
      schedule.slice(0, 3).forEach(s => {
        console.log(`${chalk.green('✓')} ${chalk.yellow(s.localTime)} - ${chalk.dim('(convenient for all)')}`);
      });
    } else {
      console.log(chalk.yellow('⚠ No perfect times found. Consider async!'));
    }
    console.log(chalk.gray('─'.repeat(50)) + '\n');
  });

program
  .command('now')
  .description('Show current time in multiple timezones')
  .option('-tz, --timezones <tzs>', 'Timezones (comma-separated)', 'kl,sg,ny,london')
  .action((options) => {
    const tzs = options.timezones.split(',').map((t: string) => t.trim());
    const results = TimezoneConverter.convert(new Date().toISOString(), 'utc', tzs);

    console.log(`\n${chalk.bold.cyan('🌍 Current Time Worldwide')}`);
    console.log(chalk.gray('─'.repeat(50)));
    
    results.forEach(r => {
      console.log(`${chalk.green(r.timezone.toUpperCase().padEnd(8))} ${chalk.yellow(r.formatted)}`);
    });
    console.log(chalk.gray('─'.repeat(50)) + '\n');
  });

program.parse(process.argv);
