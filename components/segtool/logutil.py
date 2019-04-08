"""Loging facility
"""

import logging


class DecoratedFormatter(logging.Formatter):
    """Decorates the default logging.Formatter.format
    to give relative time variables
    """

    def format(self, record):
        """Intercepts records, adds new variable relativeCreated2,
        encoding creation in mins/secs/msecs, than calls
        logging.Formatter.format() with the extended record
        """
        time = int(record.relativeCreated)
        record.relmin = time // 60000
        record.relsec = (time % 60000) // 1000
        record.relmsec = (time % 60000) % 1000
        record.reltsec = ((time % 60000) % 1000) // 100

        # record.relativeCreated2 = '[{:>-3}:{:>02}.{:>03}]'.format(
        #    mins, secs, msecs)

        return super().format(record)


def setup_logging(global_level=logging.DEBUG,
                  stdio_log=True, logfile_path=None):
    """Sets up stream handlers and global debug level
    """
    root_logger = logging.getLogger('')
    root_logger.addHandler(logging.NullHandler())

    root_logger.setLevel(global_level)

    logmsg_fmt = DecoratedFormatter(
        '<%(relmin)3d:%(relsec)2d.%(reltsec)1d' +\
        ' %(name)s-%(levelname)s> %(message)s')

    if stdio_log:
        console_log = logging.StreamHandler()
        console_log.setFormatter(logmsg_fmt)
        root_logger.addHandler(console_log)

    if not logfile_path is None:
        file_log = logging.FileHandler(str(logfile_path), 'w')
        file_log.name = 'file'
        file_log.setFormatter(logmsg_fmt)
        root_logger.addHandler(file_log)

def get_logger_name(name, domain=None):
    if not domain is None:
        if not domain.endswith('.'):
            domain += '.'
        res = domain + '{}'
    else:
        res = '{}'
    return res.format(name)


if __name__ == '__main__':
    import IPython as ip

    def get_logger():
        """Logger for testing
        """
        setup_logging()
        alog = logging.getLogger('app')
        mlog = logging.getLogger('app.mod')
        return alog, mlog

    ip.embed()
