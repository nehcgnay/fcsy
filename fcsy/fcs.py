# -*- coding: utf-8 -*-

"""Main module."""
from io import BytesIO, StringIO
import struct
from collections import namedtuple
import numpy as np


class HeaderSegment:
    ranges = {
        "version": (0, 5),
        "text_start": (10, 17),
        "text_end": (18, 25),
        "data_start": (26, 33),
        "data_end": (34, 41),
        "analysis_start": (42, 49),
        "analysis_end": (50, 57),
    }

    def __init__(
        self,
        text_start: int,
        text_end,
        data_start,
        data_end,
        analysis_start=0,
        analysis_end=0,
        ver: str = "FCS3.1",
    ) -> None:
        self.ver = ver
        self.text_start = text_start
        self.text_end = text_end
        self.data_start = data_start
        self.data_end = data_end
        self.analysis_start = analysis_start
        self.analysis_end = analysis_end

    def asdict(self):
        return {
            "text_start": self.text_start,
            "text_end": self.text_end,
            "data_start": self.data_start,
            "data_end": self.data_end,
            "analysis_start": self.analysis_start,
            "analysis_end": self.analysis_end,
        }

    @classmethod
    def from_string(cls, s: bytes):
        s = s.decode("UTF-8")
        v = dict()
        for key, value in cls.ranges.items():
            v[key] = s[value[0] : value[1] + 1].strip()
            if key != "version":
                v[key] = int(v[key])

        ver = v.pop("version")
        return HeaderSegment(
            v["text_start"],
            v["text_end"],
            v["data_start"],
            v["data_end"],
            v["analysis_start"],
            v["analysis_end"],
            ver=ver,
        )

    def _write_locations(self, sp: StringIO, type: str):
        sp.seek(self.ranges[f"{type}_start"][0])
        start_str = str(self.asdict()[f"{type}_start"])
        if len(start_str) > 8:
            start_str = "0"
        sp.write((8 - len(start_str)) * " " + start_str)
        sp.seek(self.ranges[f"{type}_end"][0])
        end_str = str(self.asdict()[f"{type}_end"])
        if len(end_str) > 8:
            end_str = "0"
        sp.write((8 - len(end_str)) * " " + end_str)

    def to_string(self):
        header = None
        with StringIO() as sp:
            sp.write(self.ver)
            sp.write(" " * 4)
            for t in ["text", "data", "analysis"]:
                self._write_locations(sp, t)
            header = sp.getvalue()

        return header


class TextSegment:
    def __init__(
        self,
        tot: int,
        pnn: list,
        pns: list,
        pnr: list,
        pne: list = None,
        mode: str = "L",
        next_data: int = 0,
        byte_order: str = "1,2,3,4",
        text_start=256,
        delim="/",
        datatype="F",
        data_start=None,
        data_end=None,
        analysis_start=None,
        analysis_end=None,
        stext_start=None,
        stext_end=None,
    ) -> None:
        self.tot = tot
        self.pnn = pnn
        self.pns = pns
        self.pnb = "32"
        self.pne = pne
        self.pnr = pnr
        self.mode = mode
        self.next_data = next_data
        self.byte_order = "1,2,3,4"
        self.text_start = text_start
        self.delim = delim
        self.datatype = datatype
        self.endian = {"1,2,3,4": "<", "4,3,2,1": ">"}[byte_order]
        self._data_start = data_start
        self._data_end = data_end
        self._analysis_start = analysis_start
        self._analysis_end = analysis_end
        self._stext_start = stext_start
        self._stext_end = stext_end
        self.text = self.build()

    def build(self):
        text = {}
        text["BYTEORD"] = self.byte_order
        text["DATATYPE"] = self.datatype
        text["MODE"] = self.mode
        text["NEXTDATA"] = str(self.next_data)
        text["BEGINANALYSIS"] = (
            str(self._analysis_start) if self._analysis_start is not None else "0"
        )
        text["ENDANALYSIS"] = (
            str(self._analysis_end) if self._analysis_end is not None else "0"
        )
        text["BEGINDATA"] = (
            str(self._data_start) if self._data_start is not None else "0"
        )
        text["ENDDATA"] = str(self._data_end) if self._data_end is not None else "0"
        text["BEGINSTEXT"] = (
            str(self._stext_start) if self._stext_start is not None else "0"
        )
        text["ENDSTEXT"] = str(self._stext_end) if self._stext_end is not None else "0"

        text["PAR"] = str(len(self.pnn))
        text["TOT"] = str(self.tot)

        for i, _ in enumerate(self.pnn):
            text["P%dB" % (i + 1)] = self.pnb
            text["P%dE" % (i + 1)] = self.pne
            text["P%dR" % (i + 1)] = str(int(self.pnr[i]))
            text["P%dN" % (i + 1)] = self.pnn[i]
            text["P%dS" % (i + 1)] = self.pns[i]

        if self._data_start is None and self._data_end is None:
            max_text_end = self.cal_max_text_ends(text, self.delim, self.text_start)
            datasize = 4 * len(self.pnn) * self.tot  # 4 is bytes to hold float
            data_start, data_end = self.cal_datapos(max_text_end + 1, datasize)
            text["BEGINDATA"] = data_start
            text["ENDDATA"] = data_end
        return text

    @property
    def data_start(self):
        return self.text["BEGINDATA"]

    @property
    def data_end(self):
        return self.text["ENDDATA"]

    @property
    def text_end(self):
        return len(self.dict_to_string(self.text, self.delim)) + self.text_start - 1

    @classmethod
    def cal_max_text_ends(cls, text, delim, text_start):
        s = cls.dict_to_string(
            {
                **text,
                "BEGINANALYSIS": "99999999",
                "ENDANALYSIS": "99999999",
                "BEGINDATA": "99999999",
                "ENDDATA": "99999999",
                "BEGINSTEXT": "99999999",
                "ENDSTEXT": "99999999",
            },
            delim,
        )
        return text_start + len(s) - 1

    def to_string(self):
        return self.dict_to_string(self.text, self.delim)

    @classmethod
    def from_string(self, s):
        delim = s[:1]
        keyvalarray = s[1:].split(delim)
        for num, i in enumerate(keyvalarray):
            try:
                keyvalarray[num] = i.decode("UTF-8")
            except UnicodeDecodeError:
                # print(num, i)
                pass

        vars = {}
        for k, v in zip(keyvalarray[::2], keyvalarray[1::2]):
            vars[k[1:]] = v

        long_channels = list()
        short_channels = list()
        max_values = list()
        for n in range(int(vars.pop("PAR"))):
            long_channels.append(vars.pop("P%dN" % (n + 1)))
            short_channels.append(
                vars.pop("P%dS" % (n + 1)) if "P%dS" % (n + 1) in vars else " "
            )
            max_values.append(int(vars.pop("P%dR" % (n + 1))))

        return TextSegment(
            int(vars["TOT"]),
            long_channels,
            short_channels,
            max_values,
            mode=vars["MODE"],
            next_data=vars["NEXTDATA"],
            byte_order=vars["BYTEORD"],
            delim=delim,
            datatype=vars["DATATYPE"],
            data_start=vars["BEGINDATA"],
            data_end=["ENDDATA"],
            analysis_start=vars["BEGINANALYSIS"],
            analysis_end=vars["ENDANALYSIS"],
            stext_start=vars["BEGINSTEXT"],
            stext_end=vars["ENDSTEXT"]            
        )

    @classmethod
    def dict_to_string(cls, dict_, delim):
        s = delim
        for i in dict_:
            s += "$%s%s%s%s" % (i, delim, dict_[i], delim)
        return s

    @classmethod
    def cal_datapos(cls, textend, datasize):
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


class DataSegment:
    def __init__(
        self, values: np.ndarray, datatype, num_dims, num_rows, endian
    ) -> None:
        self.values = values
        self.datatype = datatype
        self.num_dims = num_dims
        self.num_rows = num_rows
        self.endian = endian

    def to_string(self):
        format_ = self.endian + str(self.num_dims) + self.datatype.lower()
        s = b""
        for i in range(self.num_rows):
            s += struct.pack(format_, *self.values[i])
        return s

    @classmethod
    def from_string(cls, s: str, datatype, num_dims, num_rows, endian):
        data = BytesIO(s)
        format_ = endian + str(num_dims) + datatype.lower()
        datasize = struct.calcsize(format_)
        events = []
        for e in range(num_rows):
            read_data = data.read(datasize)
            event = struct.unpack(format_, read_data)
            events.append(event)
        values = np.array(events, dtype=np.float32 if datatype == "F" else np.float64)
        return DataSegment(values, datatype, num_dims, num_rows, endian)


class Fcs:
    def __init__(
        self,
        values: np.ndarray,
        short_channels: list,
        long_channels: list = None,
        ver: str = "FCS3.1",
        mode: str = "L",
        byte_order: str = "1,2,3,4",
        text_start: int = 256,
        datatype: str = "F",
    ) -> None:
        self.values = values
        self.short_channels = short_channels
        if long_channels is not None:
            self.long_channels = long_channels
        else:
            self.long_channels = [" " for _ in range(len(short_channels))]
        self.ver = ver
        self.mode = mode
        self.byte_order = byte_order

        self.tseg = TextSegment(
            values.shape[0],
            self.short_channels,
            self.long_channels,
            values.max(axis=0),
            mode=mode,
            byte_order=byte_order,
            text_start=text_start,
            datatype=datatype,
        )

        self.hseg = HeaderSegment(
            self.tseg.text_start,
            self.tseg.text_end,
            self.tseg.data_start,
            self.tseg.data_end,
            ver=self.ver,
        )

        self.dseg = DataSegment(
            values, datatype, values.shape[1], values.shape[0], self.tseg.endian
        )

    @classmethod
    def from_file(cls, filename, file_opener=open):
        with file_opener(filename, "rb") as fp:
            header = HeaderSegment.from_string(fp.read(58))
            fp.seek(header.text_start)
            fseg = TextSegment.from_string(
                fp.read(header.text_end - header.text_start + 1)
            )
            data_start = (
                header.data_start if header.data_start != 0 else fseg.data_start
            )
            data_end = header.data_end if header.data_end != 0 else fseg.data_end
            fp.seek(data_start)
            data = DataSegment.from_string(
                fp.read(data_end - data_start + 1),
                fseg.datatype,
                len(fseg.pnn),
                fseg.tot,
                fseg.endian,
            )

        return Fcs(data.values, fseg.pnn, fseg.pns)

    @classmethod
    def read_text_segment(cls, filename):
        with open(filename, "rb") as fp:
            header = HeaderSegment.from_string(fp.read(58))
            fp.seek(header.text_start)
            fseg = TextSegment.from_string(
                fp.read(header.text_end - header.text_start + 1)
            )
        return fseg

    def write_bytes(self, f, s):
        if not type(s) == bytes:
            f.write(s.encode("UTF-8"))
        else:
            f.write(s)

    def export(self, name):
        with open(name, "wb") as fh:
            self.write_bytes(fh, self.hseg.to_string())
            fh.seek(58)
            self.write_bytes(fh, " " * (self.tseg.text_start - fh.tell()))
            self.write_bytes(fh, self.tseg.to_string())
            self.write_bytes(fh, " " * (self.tseg.data_start - fh.tell()))
            self.write_bytes(fh, self.dseg.to_string())

    @property
    def count(self):
        return self.tseg.tot


class FcsReader:
    HeaderTuple = namedtuple(
        "Header",
        [
            "version",
            "text_start",
            "text_end",
            "data_start",
            "data_end",
            "analysis_start",
            "analysis_end",
        ],
    )

    def __init__(self):
        # self.numDims = int(self.fcsVars['$PAR'])
        pass

    def _read_fcs_vars(self, fp):
        header = self._analyze_header(fp)
        fp.seek(header.text_start)
        fcs_vars, _ = self._analyze_text(fp, header.text_start, header.text_end)
        return fcs_vars

    def count(self, filename):
        with open(filename, "rb") as fp:
            fcs_vars = self._read_fcs_vars(fp)
            return int(fcs_vars["$TOT"])

    def header(self, filename):
        with open(filename, "rb") as fp:
            fcs_vars = self._read_fcs_vars(fp)
            return self._analyze_chn(fcs_vars)

    def long_header(self, filename):
        with open(filename, "rb") as fp:
            fcs_vars = self._read_fcs_vars(fp)
            return self._analyze_chn_long(fcs_vars)

    def data(self, filename):
        with open(filename, "rb") as fp:
            header = self._analyze_header(fp)
            fp.seek(header.text_start)
            fcs_vars, _ = self._analyze_text(fp, header.text_start, header.text_end)

        data_start = header.data_start
        data_end = header.data_end
        if data_start == 0 and data_end == 0:
            data_start = int(fcs_vars["$BEGINDATA"])
            data_end = int(fcs_vars["$ENDDATA"])
        num_dims = int(fcs_vars["$PAR"])
        num_events = int(fcs_vars["$TOT"])

        with open(filename, "rb") as fcs:
            fcs.seek(data_start)
            data = fcs.read(data_end - data_start + 1)
            # Determine data format
            datatype = fcs_vars["$DATATYPE"]
            if datatype == "F":
                datatype = "f"
            elif datatype == "D":
                datatype = "d"
            endian = fcs_vars["$BYTEORD"]
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
        for n in range(1, int(fcs_vars["$PAR"]) + 1):
            try:
                if fcs_vars["$P{0}S".format(n)] not in ["", " "]:
                    channel = fcs_vars["$P{0}S".format(n)]
                else:
                    channel = fcs_vars["$P{0}N".format(n)]
            except KeyError:
                channel = fcs_vars["$P{0}N".format(n)]
            channels.append(str(channel))
        return channels

    def _analyze_chn_long(self, fcs_vars):
        channels = list()
        for n in range(1, int(fcs_vars["$PAR"]) + 1):
            channel = fcs_vars["$P{0}N".format(n)]
            channels.append(str(channel))
        return channels

    def _analyze_header(self, fp):
        header = fp.read(58)
        version = header[0:6].strip()
        text_start = int(header[10:18].strip())
        text_end = int(header[18:26].strip())
        data_start = int(header[26:34].strip())
        data_end = int(header[34:42].strip())
        analysis_start = int(header[42:50].strip())
        analysis_end = int(header[50:58].strip())
        return self.HeaderTuple(
            version,
            text_start,
            text_end,
            data_start,
            data_end,
            analysis_start,
            analysis_end,
        )

    def _analyze_text(self, fp, text_start, text_end):
        delimeter = fp.read(1)
        text = fp.read(text_end - text_start + 1)
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
            f.write(s.encode("UTF-8"))
        else:
            f.write(s)

    def build_headsg(self):
        ver = "FCS3.1"
        spaces = " " * 4
        return ver.encode("UTF-8") + spaces.encode("ASCII")

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
            rslt += "$%s%s%s%s" % (i, delim, dict_[i], delim)
        size = len(rslt)
        return size, rslt

    def export(self, name, pnts, channels, chns_short=None, extra=None):
        # magic fcs defined positions
        header_text_start = (10, 17)
        header_text_end = (18, 25)
        header_data_start = (26, 33)
        header_data_end = (34, 41)
        header_analysis_start = (42, 49)
        header_analysis_end = (50, 58)

        fh = open(name, "wb")
        self.write_bytes(fh, "FCS3.1")
        self.write_bytes(fh, " " * 53)

        # WRITE TEXT Segment
        text_start = 256  # arbitrarilly start at byte 256.
        delim = "/"  # use / as our delimiter.
        # write spaces untill the start of the txt segment
        fh.seek(58)
        self.write_bytes(fh, " " * (text_start - fh.tell()))

        nchannels = pnts.shape[1]
        npnts = pnts.shape[0]
        datasize = 4 * nchannels * npnts  # 4 is bytes to hold float

        text = {}
        text["BEGINANALYSIS"] = "0"
        text["BEGINDATA"] = "0"
        text["BEGINSTEXT"] = "0"
        text["BYTEORD"] = "1,2,3,4"  # little endian
        text["DATATYPE"] = "F"  # only do float data
        text["ENDANALYSIS"] = "0"
        text["ENDDATA"] = "0"
        text["ENDSTEXT"] = "0"
        text["MODE"] = "L"  # only do list mode data
        text["NEXTDATA"] = "0"
        text["PAR"] = str(nchannels)
        text["TOT"] = str(npnts)

        if chns_short is None:
            chns_short = channels

        for i in range(nchannels):
            text["P%dB" % (i + 1)] = "32"  # datatype =f requires 32 bits
            text["P%dE" % (i + 1)] = "0,0"
            text["P%dR" % (i + 1)] = str(int(pnts[:, i].max()))
            text["P%dN" % (i + 1)] = channels[i]
            text["P%dS" % (i + 1)] = chns_short[i]

        if extra is not None:
            for i in extra:
                i = i.strip()
                if i.lower() not in text and i.upper() not in text:
                    text[i] = extra[i]

        size, _ = self.text_size(text, delim)
        data_start, data_end = self.cal_datapos(text_start + size, datasize)
        # prop_size = text_start+(int(size/256)+1) * 256
        # prop_size = text_start+size
        text["BEGINDATA"] = data_start
        text["ENDDATA"] = data_end
        # data_start = prop_size
        # data_end = prop_size+datasize-1
        size, text_segment = self.text_size(text, delim)
        text_end = text_start + size - 1

        self.write_bytes(fh, text_segment)
        self.write_bytes(fh, " " * (data_start - fh.tell()))
        self.write_bytes(fh, pnts.astype("<f").tobytes())

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
