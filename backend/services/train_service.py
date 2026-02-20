from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Mumbai Central Line — bidirectional mock schedule
# Covers:  CSMT → Kalyan  and  Kalyan → CSMT  (reversed timings)
# Stations in order CSMT→Kalyan:
#   CSMT, Dadar, Kurla, Ghatkopar, Vidyavihar, Thane, Dombivli, Kalyan
# ---------------------------------------------------------------------------

# Travel offsets in minutes from the FIRST station (CSMT for up, Kalyan for dn)
UP_OFFSETS = {           # CSMT → Kalyan direction
    'fast': {
        'CSMT': 0, 'Dadar': 10, 'Kurla': 18,
        'Ghatkopar': 24, 'Vidyavihar': 27,
        'Thane': 40, 'Dombivli': 55, 'Kalyan': 65,
    },
    'slow': {
        'CSMT': 0, 'Dadar': 14, 'Kurla': 22,
        'Ghatkopar': 30, 'Vidyavihar': 33,
        'Thane': 55, 'Dombivli': 68, 'Kalyan': 80,
    },
}

# Down direction: Kalyan → CSMT (just mirror the offsets)
DN_OFFSETS = {
    'fast': {st: (65 - off) for st, off in UP_OFFSETS['fast'].items()},
    'slow': {st: (80 - off) for st, off in UP_OFFSETS['slow'].items()},
}

STATION_ORDER = ['CSMT', 'Dadar', 'Kurla', 'Ghatkopar', 'Vidyavihar',
                 'Thane', 'Dombivli', 'Kalyan']


class TrainService:
    def __init__(self):
        self.stations = STATION_ORDER
        # Generate once; keyed by direction: 'up' or 'dn'
        self.schedules = {
            'up': self._generate_schedule('up'),
            'dn': self._generate_schedule('dn'),
        }

    # ------------------------------------------------------------------
    def _generate_schedule(self, direction: str):
        """Generate trains from 04:00 to 24:00 every 10 minutes."""
        offsets = UP_OFFSETS if direction == 'up' else DN_OFFSETS
        origin = 'CSMT' if direction == 'up' else 'Kalyan'

        schedule = []
        base = datetime.now().replace(hour=4, minute=0, second=0, microsecond=0)
        end  = base + timedelta(hours=20)

        current = base
        train_type_toggle = True   # alternate fast/slow
        while current < end:
            ttype = 'fast' if train_type_toggle else 'slow'
            train_type_toggle = not train_type_toggle
            off = offsets[ttype]

            stations_times = {
                st: (current + timedelta(minutes=mins)).strftime('%H:%M')
                for st, mins in off.items()
            }

            prefix = ('F' if ttype == 'fast' else 'S') + ('U' if direction == 'up' else 'D')
            schedule.append({
                'train_id': f"{prefix}{current.strftime('%H%M')}",
                'type':     ttype.capitalize(),
                'direction': direction,
                'origin':   origin,
                'stations': stations_times,
            })
            current += timedelta(minutes=5)

        return schedule

    # ------------------------------------------------------------------
    def _direction(self, source: str, destination: str) -> str:
        """Return 'up' or 'dn' based on station order."""
        try:
            si = STATION_ORDER.index(source)
            di = STATION_ORDER.index(destination)
        except ValueError:
            return 'up'  # fallback
        return 'up' if di > si else 'dn'

    # ------------------------------------------------------------------
    def get_next_trains(self, source: str, destination: str,
                        after_time_str: str = None, limit: int = 5):
        """
        Return up to `limit` trains from source to destination
        departing at or after `after_time_str` (HH:MM).
        """
        if after_time_str:
            query_time = datetime.strptime(after_time_str, '%H:%M').time()
        else:
            query_time = datetime.now().time()

        direction = self._direction(source, destination)
        trains = self.schedules[direction]

        results = []
        for train in trains:
            if source not in train['stations'] or destination not in train['stations']:
                continue

            dept_str = train['stations'][source]
            arr_str  = train['stations'][destination]
            dept_t   = datetime.strptime(dept_str, '%H:%M').time()

            if dept_t < query_time:
                continue

            dept_dt = datetime.combine(datetime.today(), dept_t)
            arr_dt  = datetime.combine(datetime.today(),
                                       datetime.strptime(arr_str, '%H:%M').time())
            duration_mins = int((arr_dt - dept_dt).total_seconds() / 60)

            results.append({
                'train_id':      train['train_id'],
                'type':          train['type'],
                'departure':     dept_str,
                'arrival':       arr_str,
                'duration_mins': duration_mins,
            })

            if len(results) >= limit:
                break

        return results
