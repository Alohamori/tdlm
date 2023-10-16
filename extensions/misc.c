#define _XOPEN_SOURCE

#include <assert.h>
#include <ctype.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "sqlite3ext.h"
SQLITE_EXTENSION_INIT1

static bool
is_prime(int n) {
    if (n < 2) return false;

    int i = 2;
    while (i*i <= n)
        if (n % i++ == 0) return false;

    return true;
}

static int
letsum(char *w)
{
    int sum = 0;
    for (char *c = w; *c; ++c)
        if (isalpha(*c))
            sum += *c & 31;
    return sum;
}

static const char *weekdays[] = {"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"};
static const int wdaylens[] = {6, 6, 7, 9, 8, 6, 8};

static int
weekday(const char *d) {
    char w[2];
    struct tm t;
    strptime(d, "%Y-%m-%d", &t);
    strftime(w, 2, "%w", &t);
    return *w - 48;
}

static int
datediff(const char *a, const char *b)
{
    int ya, ma, da, yb, mb, db, diff;
    int x = sscanf(a, "%d-%d-%d", &ya, &ma, &da);
    if (x < 3) da = 1; if (x < 2) ma = 1;
    x = sscanf(b, "%d-%d-%d", &yb, &mb, &db);
    if (x < 3) db = 1; if (x < 2) mb = 1;

    diff = ya - yb;
    if (mb > ma || (ma == mb && db > da)) --diff;
    return diff;
}

static int
mindaydiff(const char *s, const char *t)
{
    int min = 420, diff;
    struct tm a = {}, b = {};
    strptime(s, "%F", &a);
    strptime(t, "%F", &b);

    for (int i = -1; i < 2; ++i) {
        b.tm_year = a.tm_year + i;
        diff = abs((mktime(&b) - mktime(&a)) / 86400);
        if (diff < min) min = diff;
    }

    return min;
}

static void
primefunc(sqlite3_context *context, int argc, sqlite3_value **argv) {
  assert(argc == 1);
  if (sqlite3_value_type(argv[0]) != SQLITE_INTEGER) return;

  int n = sqlite3_value_int(argv[0]);
  sqlite3_result_int(context, is_prime(n));
}

static void
weekdayfunc(sqlite3_context *context, int argc, sqlite3_value **argv) {
  assert(argc == 1);
  if (sqlite3_value_type(argv[0]) != SQLITE_TEXT) return;

  const unsigned char *d = sqlite3_value_text(argv[0]);
  const int w = weekday((char *) d);
  sqlite3_result_text(context, weekdays[w], wdaylens[w], SQLITE_TRANSIENT);
}

static void
letsumfunc(sqlite3_context *context, int argc, sqlite3_value **argv) {
  assert(argc == 1);
  if (sqlite3_value_type(argv[0]) != SQLITE_TEXT) return;

  const unsigned char *d = sqlite3_value_text(argv[0]);
  const int w = letsum((char *) d);
  sqlite3_result_int(context, w);
}


static void
datedifffunc(sqlite3_context *context, int argc, sqlite3_value **argv) {
  assert(argc == 2);
  if (sqlite3_value_type(argv[0]) != SQLITE_TEXT) return;
  if (sqlite3_value_type(argv[1]) != SQLITE_TEXT) return;

  const unsigned char *a = sqlite3_value_text(argv[0]);
  const unsigned char *b = sqlite3_value_text(argv[1]);
  const int diff = datediff(a, b);
  sqlite3_result_int(context, diff);
}

static void
mindaydifffunc(sqlite3_context *context, int argc, sqlite3_value **argv) {
  assert(argc == 2);
  if (sqlite3_value_type(argv[0]) != SQLITE_TEXT) return;
  if (sqlite3_value_type(argv[1]) != SQLITE_TEXT) return;

  const unsigned char *a = sqlite3_value_text(argv[0]);
  const unsigned char *b = sqlite3_value_text(argv[1]);
  const int diff = mindaydiff(a, b);
  sqlite3_result_int(context, diff);
}

int
sqlite3_mine_init(sqlite3 *db, char **u, const sqlite3_api_routines *pApi) {
  (void)u;
  SQLITE_EXTENSION_INIT2(pApi);
  sqlite3_create_function(db, "prime", 1, SQLITE_INNOCUOUS|SQLITE_DETERMINISTIC, 0, primefunc, 0, 0);
  sqlite3_create_function(db, "weekday", 1, SQLITE_INNOCUOUS|SQLITE_DETERMINISTIC, 0, weekdayfunc, 0, 0);
  sqlite3_create_function(db, "letsum", 1, SQLITE_INNOCUOUS|SQLITE_DETERMINISTIC, 0, letsumfunc, 0, 0);
  sqlite3_create_function(db, "datediff", 2, SQLITE_INNOCUOUS|SQLITE_DETERMINISTIC, 0, datedifffunc, 0, 0);
  sqlite3_create_function(db, "mindaydiff", 2, SQLITE_INNOCUOUS|SQLITE_DETERMINISTIC, 0, mindaydifffunc, 0, 0);

  return SQLITE_OK;
}
