# -*- coding: utf-8 -*-

"""Main module."""
from io import BytesIO
import struct
from collections import namedtuple
from pandas import DataFrame as pdDataFrame


def read_fcs_names(f, name_type='short'):
    reader = FcsReader()
    mapping = {'short': reader.header, 'long': reader.long_header}
    return mapping[name_type](f)


def read_fcs(f, name_type='short'):
    reader = FcsReader()
    data = reader.data(f)
    columns = read_fcs_names(f, name_type=name_type)

    return pdDataFrame(data, columns=columns)


def write_fcs(df, path, long_names=None):
    write = FcsWriter()
    long_names = df.columns if long_names == None else long_names
    write.export(path, df.loc[:].values,
                 long_names, df.columns)


class FcsReader:
    HeaderTuple = namedtuple('Header', ['version', 'text_start',
                                        'text_end', 'data_start', 'data_end',
                                        'analysis_start', 'analysis_end'])

    def __init__(self):
        # self.numDims = int(self.fcsVars['$PAR'])
        pass

    def count(self, filename):
        header = self._analyze_header(filename)
        fcs_vars, delimiter = self._analyze_text(filename, header.text_start,
                                                 header.text_end)
        return int(fcs_vars['$TOT'])

    def header(self, filename):
        header = self._analyze_header(filename)
        fcs_vars, delimiter = self._analyze_text(filename, header.text_start,
                                                 header.text_end)
        return self._analyze_chn(fcs_vars)

    def long_header(self, filename):
        header = self._analyze_header(filename)
        fcs_vars, delimiter = self._analyze_text(filename, header.text_start,
                                                 header.text_end)
        return self._analyze_chn_long(fcs_vars)

    def data(self, filename):
        fcs_header = self._analyze_header(filename)
        fcs_vars, delimiter = self._analyze_text(filename, fcs_header.text_start,
                                                 fcs_header.text_end)
        data_start = fcs_header.data_start
        data_end = fcs_header.data_end
        if data_start == 0 and data_end == 0:
            data_start = int(fcs_vars['$BEGINDATA'])
            data_end = int(fcs_vars['$ENDDATA'])
        num_dims = int(fcs_vars['$PAR'])
        num_events = int(fcs_vars['$TOT'])

        with open(filename, 'rb') as fcs:
            fcs.seek(data_start)
            data = fcs.read(data_end - data_start + 1)
            # Determine data format
            datatype = fcs_vars['$DATATYPE']
            if datatype == 'F':
                datatype = 'f'
            elif datatype == 'D':
                datatype = 'd'
            endian = fcs_vars['$BYTEORD']
            if endian == "4,3,2,1":
                endian = ">"
            elif endian == "1,2,3,4":
                endian = "<"

            data = BytesIO(data)
            format_ = endian + str(num_dims) + datatype
            datasize = struct.calcsize(format_)
            events = []
            for e in range(num_events):
                read_data = data.read(datasize)
                event = struct.unpack(format_, read_data)
                events.append(event)
        return events

    def _analyze_chn(self, fcs_vars):
        channels = list()
        for n in range(1, int(fcs_vars['$PAR']) + 1):
            try:
                if fcs_vars['$P{0}S'.format(n)] not in ['', ' ']:
                    channel = fcs_vars['$P{0}S'.format(n)]
                else:
                    channel = fcs_vars['$P{0}N'.format(n)]
            except KeyError:
                channel = fcs_vars['$P{0}N'.format(n)]
            channels.append(str(channel))
        return channels

    def _analyze_chn_long(self, fcs_vars):
        channels = list()
        for n in range(1, int(fcs_vars['$PAR']) + 1):
            channel = fcs_vars['$P{0}N'.format(n)]
            channels.append(str(channel))
        return channels

    def _analyze_header(self, filename):
        with open(filename, 'rb') as fcs:
            header = fcs.read(58)
            version = header[0:6].strip()
            text_start = int(header[10:18].strip())
            text_end = int(header[18:26].strip())
            data_start = int(header[26:34].strip())
            data_end = int(header[34:42].strip())
            analysis_start = int(header[42:50].strip())
            analysis_end = int(header[50:58].strip())
            return self.HeaderTuple(version,
                                    text_start, text_end,
                                    data_start, data_end,
                                    analysis_start, analysis_end)

    def _analyze_text(self, filename, text_start, text_end):
        with open(filename, 'rb') as fcs:
            fcs.seek(text_start)
            delimeter = fcs.read(1)
            text = fcs.read(text_end - text_start + 1)
        # Variables in TEXT poriton are stored "key/value/key/value/key/value"
        keyvalarray = text.split(delimeter)
        for num, i in enumerate(keyvalarray):
            try:
                keyvalarray[num] = i.decode("UTF-8")
            except UnicodeDecodeError:
                # print(num, i)
                pass
        fcsVars = {}
        fcs_var_list = []

        # Iterate over every 2 consecutive elements of the array
        for k, v in zip(keyvalarray[::2], keyvalarray[1::2]):
            fcsVars[k] = v
            fcs_var_list.append((k, v))

        return fcsVars, delimeter


class FcsWriter:
    def write_bytes(self, f, s):
        if not type(s) == bytes:
            f.write(s.encode('UTF-8'))
        else:
            f.write(s)

    def build_headsg(self):
        ver = 'FCS3.1'
        spaces = ' ' * 4
        return ver.encode('UTF-8') + spaces.encode('ASCII')

    def cal_datapos(self, textend, datasize):
        start = 0
        end = 0
        start_new = textend + 1
        end_new = start_new + datasize - 1

        while True:
            inc_start = len(str(start_new)) - len(str(start))
            inc_end = len(str(end_new)) - len(str(end))
            start = start_new
            end = end_new

            if inc_start + inc_end > 0:
                start_new = inc_start + inc_end + start
                end_new = start_new + datasize - 1
            else:
                break

        return start, end

    def text_size(self, dict_, delim):
        rslt = delim
        for i in dict_:
            rslt += '$%s%s%s%s' % (i, delim, dict_[i], delim)
        size = len(rslt)
        return size, rslt

    def export(self, name, pnts, channels,
               chns_short=None, extra=None):
        # magic fcs defined positions
        header_text_start = (10, 17)
        header_text_end = (18, 25)
        header_data_start = (26, 33)
        header_data_end = (34, 41)
        header_analysis_start = (42, 49)
        header_analysis_end = (50, 58)

        fh = open(name, 'wb')
        self.write_bytes(fh, 'FCS3.1')
        self.write_bytes(fh, ' ' * 53)

        ## WRITE TEXT Segment
        text_start = 256  # arbitrarilly start at byte 256.
        delim = '/'  # use / as our delimiter.
        # write spaces untill the start of the txt segment
        fh.seek(58)
        self.write_bytes(fh, ' ' * (text_start - fh.tell()))

        nchannels = pnts.shape[1]
        npnts = pnts.shape[0]
        datasize = 4 * nchannels * npnts  # 4 is bytes to hold float

        text = {}
        text['BEGINANALYSIS'] = '0'
        text['BEGINDATA'] = '0'
        text['BEGINSTEXT'] = '0'
        text['BYTEORD'] = '1,2,3,4'  # little endian
        text['DATATYPE'] = 'F'  # only do float data
        text['ENDANALYSIS'] = '0'
        text['ENDDATA'] = '0'
        text['ENDSTEXT'] = '0'
        text['MODE'] = 'L'  # only do list mode data
        text['NEXTDATA'] = '0'
        text['PAR'] = str(nchannels)
        text['TOT'] = str(npnts)

        if chns_short is None:
            chns_short = channels

        for i in range(nchannels):
            text['P%dB' % (i + 1)] = '32'  # datatype =f requires 32 bits
            text['P%dE' % (i + 1)] = '0,0'
            text['P%dR' % (i + 1)] = str(int(pnts[:, i].max()))
            text['P%dN' % (i + 1)] = channels[i]
            text['P%dS' % (i + 1)] = chns_short[i]

        if extra is not None:
            for i in extra:
                i = i.strip()
                if i.lower() not in text and i.upper() not in text:
                    text[i] = extra[i]

        size, _ = self.text_size(text, delim)
        data_start, data_end = self.cal_datapos(text_start + size, datasize)
        # prop_size = text_start+(int(size/256)+1) * 256
        # prop_size = text_start+size
        text['BEGINDATA'] = data_start
        text['ENDDATA'] = data_end
        # data_start = prop_size
        # data_end = prop_size+datasize-1
        size, text_segment = self.text_size(text, delim)
        text_end = text_start + size - 1

        self.write_bytes(fh, text_segment)
        self.write_bytes(fh, ' ' * (data_start - fh.tell()))
        self.write_bytes(fh, pnts.astype('<f').tostring())

        fh.seek(header_text_start[0])
        self.write_bytes(fh, str(text_start))
        fh.seek(header_text_end[0])
        self.write_bytes(fh, str(text_end))

        fh.seek(header_data_start[0])
        if len(str(data_end)) < (header_data_end[1] - header_data_end[0]):
            self.write_bytes(fh, str(data_start))
            fh.seek(header_data_end[0])
            self.write_bytes(fh, str(data_end))
        else:
            self.write_bytes(fh, str(0))
            fh.seek(header_data_end[0])
            self.write_bytes(fh, str(0))

        fh.seek(header_analysis_start[0])
        self.write_bytes(fh, str(0))
        fh.seek(header_analysis_end[0])
        self.write_bytes(fh, str(0))

        fh.close()



