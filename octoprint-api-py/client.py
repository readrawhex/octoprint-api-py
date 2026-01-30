import requests


class Client:
    """
    Defines the client used for making requests to
    the octoprint server.
    """

    def __init__(self, base_url: str, api_key: str = None):
        self._api_key = api_key
        self._base_url = base_url

    def _make_request(self, endpoint: str, method: str = "GET", **kwargs):
        """
        make request to Octoprint with `self._api_key` included
        in `X-Api-Key` header.
        """
        if "headers" in kwargs.keys():
            headers = kwargs.pop("headers")
            headers["X-Api-Key"] = self.api_key
        else:
            headers = {
                "X-Api-Key": self.api_key,
            }
        url = urllib.parse.urljoin(self.url, endpoint)
        resp = requests.request(method, url, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp

    def version(self):
        """
        Retrieve Octoprint version information.

        - endpoint: `/api/version`
        - method: `GET`
        """
        resp = self._make_request("/api/version")
        return resp.json

    def server(self):
        """
        Retrieve Octoprint connection information.

        - endpoint: `/api/server`
        - method: `GET`
        """
        resp = self._make_request("/api/server")
        return resp.json

    def connect_settings(self):
        """
        Retrieve Octoprint connection settings.

        - endpoint: `/api/connection`
        - method: `GET`
        """
        resp = self._make_request("/api/server")
        return resp.json

    def connect(
        self,
        port: str = None,
        baudrate: int = None,
        printerProfile: str = None,
        save: bool = False,
        autoconnect: bool = None,
    ):
        """
        Instructs OctoPrint to connect or, if already connected, reconnect to
        the printer.

        - endpoint: `/api/connection`
        - method: `POST`

        params:
            port (str): Optional, specific port to connect to.
                If not set the current portPreference will be used,
                or if no preference is available auto detection will
                be attempted.
            baudrate (int): Optional, specific baudrate to connect with.
                If not set the current baudratePreference will be used,
                or if no preference is available auto detection will be
                attempted.
            printerProfile (str): Optional, specific printer profile to
                use for connection. If not set the current default
                printer profile will be used.
            save (bool): Optional, whether to save the request’s port
                and baudrate settings as new preferences. Defaults to
                false if not set.
            autoconnect (bool): Optional, whether to automatically
                connect to the printer on OctoPrint’s startup in the
                future. If not set no changes will be made to the
                current configuration.
        """
        data = {"command": "connect"}
        if port:
            data["port"] = port
        if baudrate:
            data["baudrate"] = baudrate
        if printerProfile:
            data["printerProfile"] = printerProfile
        if save:
            data["save"] = save
        if autoconnect:
            data["autoconnect"] = autoconnect
        resp = self._make_request("/api/connection", "POST", json=data)

    def disconnect(self):
        """
        Instructs OctoPrint to disconnect from the printer.

        - endpoint: `/api/connection`
        - method: POST
        """
        data = {"command": "disconnect"}
        resp = self._make_request("/api/connection", "POST", json=data)

    def files(
        self,
        override_cache: bool = False,
        recursive: bool = False,
        location: str = "local",
    ):
        """
        Retrieve information regarding all files currently available and
        regarding the disk space still available locally in the system.
        The results are cached for performance reasons.

        - endpoint: `/api/files`
        - method: `GET`

        params:
            override_cache (bool): override cache on request
            recursive (bool): return files within folders in root directory
            location (str): either `local` (uploads folder) or `sdcard`
        """
        params = {
            "force": override_cache,
            "recursive": recursive,
        }
        url = "/api/files"
        if location not in ["local", "sdcard"]:
            raise ValueError("`location` argument must be one of ['local', 'sdcard']")
        url += f"/{location}"
        resp = self._make_request(url, params=params)
        return resp.json

    def file_upload(
        self, filename: str, file, path: str = "/", location: str = "local"
    ):
        """
        Upload a file to the selected `location`.

        - endpoint: `/api/files`
        - method: `POST`

        params:
            filename (str): name for uploaded file
            file (bytes obj): actual file object to upload (bytes object)
            path (str): path to parent folder within `location` for upload.
            location (str): full path location to upload file to
        """
        if location not in ["local", "sdcard"]:
            raise ValueError("`location` path must be either 'local' or 'sdcard'")
        url = "/api/files/" + location
        resp = self._make_request(
            url,
            "POST",
            files={
                "files": (filename, file),
                "path": (None, path),
            },
        )
        return resp.json

    def new_directory(self, foldername: str, path: str = None):
        """
        Create a subfolder within the local uploads folder.

        - endpoint: `/api/files/local`
        - method: `POST`

        params:
            foldername (str): name of folder to create
            path (str): Optional, path to parent folder within uploads folder.
        """
        if foldername in [None, ""]:
            raise ValueError(f"invalid foldername: '{foldername}'")
        resp = self._make_request(
            "/api/files/local",
            files={
                "foldername": (None, foldername),
                "path": (None, path),
            },
        )
        return resp.json

    def file_retrieve(self, path: str, recursive: bool = False):
        """
        Retrieve the file located at either `local/path/to/local/file` or
        `sdcard/path/to/sdcard/file` specified in `path` argument.

        - endpoint: `/api/files/<path>`
        - method: `GET`

        params:
            path (str): path to file beginning with either `local/` or `sdcard/`
        """
        if not path.startswith("local/") and not path.startswith("sdcard/"):
            raise ValueError(f"`path` must begin with 'local/' or 'sdcard/'")
        resp = self._make_request("/api/files/" + path, params={"recursive": recursive})
        return resp.json

    def file_select(self, path: str, print_now: bool = False):
        """
        Selects a file for printing.

        - endpoint: `/api/files/<path>`
        - method: `POST`

        params:
            path (str): path to file, beginning with either 'local' or 'sdcard'
            print_now (bool): print file once selected
        """
        if not path.startswith("local/") and not path.startswith("sdcard/"):
            raise ValueError(f"`path` must begin with 'local/' or 'sdcard/'")
        resp = self._make_request(
            "/api/files/" + path,
            "POST",
            params={
                "command": "select",
                "print": print_now,
            },
        )
        return resp.json

    def file_unselect(self):
        """
        Unselects the currently selected file for printing.

        - endpoint: `/api/files/<path>`
        - method: `POST`
        """
        resp = self._make_request(
            "/api/files/" + path,
            "POST",
            params={
                "command": "unselect",
            },
        )
        return resp.json

    def file_slice(
        self,
        path: str,
        filename: str,
        position_x: int = 100,
        position_y: int = 100,
        printerProfile: str = None,
        profile: str = None,
        select: bool = False,
        print_now: bool = False,
        slicer: str = "cura",
    ):
        """
        Slices an STL file into GCODE. Note that this is an asynchronous
        operation that will take place in the background after the response
        has been sent back to the client. Additional parameters are:

        - endpoint: `/api/files/<path>`
        - method: `POST`

        params:
            path (str): path to stl file to slice to gcode
            filename (str): name of gcode file to output to
            position_x (int): x position for center of object on print bed.
            position_y (int): y position for center of object on print bed.
            printerProfile (str): printer profile to use for slicing
            profile (str): slicing profile to use for slicing
            select (bool): select file after slicing has finished
            print_now (bool): print file after slicing has finished
            slicer (str): slicing engine to use ('cura' is the only one available currently)
        """
        if not path.startswith("local/") and not path.startswith("sdcard/"):
            raise ValueError(f"`path` must begin with 'local/' or 'sdcard/'")
        data = {
            "command": "slice",
            "gcode": filename,
            "position": {"x": position_x, "y": position_y},
            "printerProfile": printerProfile,
            "profile": profile,
            "select": select,
            "print": print_now,
            "slicer": slicer,
        }
        resp = self._make_request("/api/files/" + path, "POST", json=data)
        return resp.json

    def file_delete(self, path: str):
        """
        Delete the selected file at `path`, beginning with 'local/' or 'sdcard/'.

        - endpoint: `/api/files/<path>`
        - method: `DELETE`

        params:
            path (str): path to file to delete
        """
        if not path.startswith("local/") and not path.startswith("sdcard/"):
            raise ValueError(f"`path` must begin with 'local/' or 'sdcard/'")
        resp = self._make_request("/api/files/" + path, "DELETE")

    def job_start(self):
        """
        Starts the print of the currently selected file. For selecting a file, see 
        Issue a file command. If a print job is already active, a 409 Conflict 
        will be returned.

        - endpoint: `/api/job`
        - method: `POST`
        """
        resp = self._make_request("/api/job", "POST", json={"command": "start"})

    def job_cancel(self):
        """
        Cancels the current print job. If no print job is active (either paused 
        or printing), a 409 Conflict will be returned.

        - endpoint: `/api/job`
        - method: `POST`
        """
        resp = self._make_request("/api/job", "POST", json={"command": "cancel"})

    def job_restart(self):
        """
        Restart the print of the currently selected file from the beginning. 
        There must be an active print job for this to work and the print job 
        must currently be paused. If either is not the case, a 409 Conflict 
        will be returned.

        - endpoint: `/api/job`
        - method: `POST`
        """
        resp = self._make_request("/api/job", "POST", json={"command": "restart"})

    def job_pause(self):
        """
        Pauses the current job if it’s printing, does nothing if it’s already 
        paused.

        - endpoint: `/api/job`
        - method: `POST`
        """
        resp = self._make_request("/api/job", "POST", json={"command": "pause", "action": "pause"})

    def job_resume(self):
        """
        Resumes the current job if it’s paused, does nothing if it’s already 
        printing.

        - endpoint: `/api/job`
        - method: `POST`
        """
        resp = self._make_request("/api/job", "POST", json={"command": "pause", "action": "resume"})

    def job_toggle(self):
        """
        Toggles the pause state of the job, pausing it if it’s printing and 
        resuming it if it’s currently paused.

        - endpoint: `/api/job`
        - method: `POST`
        """
        resp = self._make_request("/api/job", "POST", json={"command": "pause", "action": "toggle"})

    def job(self):
        """
        Retrieve information about the current job (if there is one).

        - endpoint: `/api/job`
        - method: `GET`
        """
        resp = self._make_request("/api/job")
        return resp.json

    def printer(self, history: int = 0, exclude: str = None):
        """
        Retrieves the current state of the printer.

        - endpoint: `/api/printer`
        - method: `GET`

        params:
            history (int): number of temperature records to include
        """
        if history is None or history < 0:
            raise ValueError("`history` must be positive int or zero")
        data = {}
        if exclude: data["exclude"] = exclude
        if history > 0:
            data["history"] = True
            data["limit"] = history
        resp = self._make_request("/api/printer", params=data)
        return resp.json

    def printhead_jog(self, x: int = None, y: int = None, z: int = None, absolute: bool = False, speed: int = None):
        """
        Jogs the print head (relatively) by a defined amount in one or more axes.

        - endpoint: `/api/printer/printhead`
        - method: `POST`

        params:
            x (int): Amount/coordinate to jog print head on x axis, 
                must be a valid number corresponding to the distance 
                to travel in mm.
            y (int): Amount/coordinate to jog print head on y axis, 
                must be a valid number corresponding to the distance 
                to travel in mm.
            z (int): Amount/coordinate to jog print head on z axis, 
                must be a valid number corresponding to the distance 
                to travel in mm.
            absolute (bool): specifies whether to move relative to 
                current position (provided axes values are relative 
                amounts) or to absolute position (provided axes values 
                are coordinates)
            speed (int): Speed at which to move. If not provided, minimum 
                speed for all selected axes from printer profile will 
                be used.
        """
        if x is None and y is None and z is None:
            raise TypeError("no `x`, `y`, or `z` argument was provided")
        data = {"command": "jog"}
        if x: data["x"] = x
        if y: data["y"] = y
        if z: data["z"] = z
        if absolute: data["absolute"] = absolute
        if speed: data["speed"] = speed
        resp = self._make_request("/api/printer/printhead", "POST", json=data)

    def printhead_home(self, x: bool = True, y: bool = True, z: bool = True):
        """
        Homes the print head in all of the given axes.

        - endpoint: `/api/printer/printhead`
        - method: `POST`

        params:
            x (bool): home the printer along the x-axis
            y (bool): home the printer along the y-axis
            z (bool): home the printer along the z-axis
        """
        if True not in [x, y, z]:
            raise TypeError("one of `x`, `y`, or `z` must be `True`")
        data = {"command": "home", "axes": []}
        if x: data["axes"].append("x") 
        if y: data["axes"].append("y") 
        if z: data["axes"].append("z") 
        resp = self._make_request("/api/printer/printhead", "POST", json=data)

    def printhead_feedrate(self, factor: float = 100.0):
        """
        Changes the feedrate factor to apply to the movements of the axes.

        - endpoint: `/api/printer/printhead`
        - method: `POST`

        params:
            factor (float): The new factor, percentage between 50 and 200% as 
            integer (50 to 200) or float (0.5 to 2.0).
        """
        if factor > 2.0:
            factor /= round(100.0, 2)
        if factor > 2.0 or factor < 0.5:
            raise ValueError("`factor` must be between [0.5, 2.0] or [50, 200].")
        resp = self._make_request("/api/printer/printhead", "POST", json={
            "command": "feedrate",
            "factor": factor,
        })

    def tool_target(self, temp):
        """
        Sets the given target temperature on the printer’s tools. Can either
        provide a zero or positive int value for `temp`, or a list of ints
        where each index N corresponds to tool{N}.

        - endpoint: `/api/printer/tool`
        - method: `POST`

        params:
            temp (int / list): temperature(s) for tool(s).
        """
        if type(temp) not in [int, list]:
            raise ValueError("`temp` must be either an integer or list object")
        elif type(temp) == int:
            data = {"command": "target", "targets": {"tool": temp}}
        else:
            targets = {}
            for i, x in enumerate(temp):
                targets[f"tool{i}"] = x
            data = {"command": "target", "targets": targets}
        resp = self._make_request("/api/printer/tool", "POST", json=data)

    def tool_offsets(self, offsets: list):
        """
        Sets the given temperature offset on the printer’s tools.

        - endpoint: `/api/printer/tool`
        - method: `POST`

        params:
            offsets (list): list of temperature offsets, with index N being 
                offset for tool N.
        """
        _offsets = {}
        for i, x in enumerate(offsets):
            _offsets[f"tool{i}"] = x
        data = {"command": "offset", "offsets": _offsets}
        resp = self._make_request("/api/printer/tool", "POST", json=data)

    def tool_select(self, tool: int):
        """
        Selects the printer’s current tool.

        - endpoint: `/api/printer/tool`
        - method: `POST`

        params:
            tool (int): index of tool to select (zero-indexed)
        """
        if tool < 0:
            raise ValueError("`tool` must be zero or positive")
        data = {"command": "select", "tool": tool}
        resp = self._make_request("/api/printer/tool", "POST", json=data)

    def tool_extrude(self, amount: int, speed: int = None):
        """
        Extrudes the given amount of filament from the currently selected tool. 

        - endpoint: `/api/printer/tool`
        - method: `POST`

        params:
            amount (int): The amount of filament to extrude in mm. May 
                be negative to retract.
            speed (int): Optional. Speed at which to extrude. If not provided, 
                maximum speed for E axis from printer profile will be used. 
                Otherwise interpreted as an integer signifying the speed in mm/min, 
                to append to the command.
        """
        data = {"command": "extrude", "amount": amount}
        if speed:
            if speed < 0:
                raise ValueError("`speed` must be zero or positive")
            data["speed"] = speed
        resp = self._make_request("/api/printer/tool", "POST", json=data)

    def tool_flowrate(self, factor: int):
        """
        Changes the flow rate factor to apply to extrusion of the tool.

        - endpoint: `/api/printer/tool`
        - method: `POST`

        params:
            factor (int): The new factor, percentage between 75 and 125% 
                as integer (75 to 125) or float (0.75 to 1.25).
        """
        if factor > 1.25:
            factor /= round(100.0, 2)
        if factor > 1.25 or factor < 0.75:
            raise ValueError("`factor` must be between [0.75, 1.25] or [75, 125].")
        resp = self._make_request("/api/printer/tool", "POST", json={
            "command": "flowrate",
            "factor": factor,
        })

    def tool(self, history: int = 0):
        """
        Retrieves the current temperature data (actual, target and offset) plus 
        optionally a (limited) history (actual, target, timestamp) for all of 
        the printer’s available tools.

        - endpoint: `/api/printer/tool`
        - method: `GET`

        params:
            history (int): number of temperature records to include
        """
        if history is None or history < 0:
            raise ValueError("`history` must be positive int or zero")
        data = {}
        if history > 0:
            data["history"] = True
            data["limit"] = history
        resp = self._make_request("/api/printer/tool", params=data)
        return resp.json

    def bed_target(self, target: int):
        """
        Sets the given target temperature on the printer’s bed.

        - endpoint: `/api/printer/bed`
        - method: `POST`

        params:
            target (int): Target temperature to set. A value of 0 will turn 
                the heater off.
        """
        if target < 0:
            raise ValueError("`target` must be zero or positive")
        data = {"command": "target", "target": target}
        resp = self._make_request("/api/printer", json=data)

    def bed_offset(self, offset: int):
        """
        Sets the given temperature offset on the printer’s bed.

        - endpoint: `/api/printer/bed`
        - method: `POST`

        params:
            offset (int): Offset to set.
        """
        data = {"command": "offset", "offset": offset}
        resp = self._make_request("/api/printer", json=data)

    def bed(self, history: int = 0):
        """
        Retrieves the current temperature data (actual, target and offset) 
        plus optionally a (limited) history (actual, target, timestamp) for 
        the printer’s heated bed.

        - endpoint: `/api/printer/bed`
        - method: `GET`

        params:
            history (int): number of temperature records to include
        """
        if history is None or history < 0:
            raise ValueError("`history` must be positive int or zero")
        data = {}
        if history > 0:
            data["history"] = True
            data["limit"] = history
        resp = self._make_request("/api/printer/bed", params=data)
        return resp.json

    # LEFT OFF AT CHAMBER COMMANDS
    # https://docs.octoprint.org/en/main/api/printer.html#issue-a-chamber-command
