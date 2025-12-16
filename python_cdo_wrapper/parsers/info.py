"""Information parsers for CDO output."""

from __future__ import annotations

import re

from ..exceptions import CDOParseError
from ..types.results import (
    InfoResult,
    PartabInfo,
    PartabResult,
    SinfoResult,
    TimestepInfo,
    VlistResult,
)
from ..types.variable import (
    DatasetVariable,
    GridCoordinates,
    TimeInfo,
    VariableInfo,
    VerticalCoordinates,
)
from .base import CDOParser


class SinfoParser(CDOParser[SinfoResult]):
    """
    Parser for sinfo command output.

    Parses comprehensive dataset summary including format, variables,
    grid coordinates, vertical coordinates, and time information.
    """

    def parse(self, output: str) -> SinfoResult:
        """
        Parse sinfo output.

        Args:
            output: Raw output from CDO sinfo command.

        Returns:
            SinfoResult containing parsed dataset information.

        Raises:
            CDOParseError: If parsing fails.
        """
        try:
            file_format = self._parse_file_format(output)
            variables = self._parse_variables(output)
            grid_coords = self._parse_grid_coordinates(output)
            vertical_coords = self._parse_vertical_coordinates(output)
            time_info = self._parse_time_coordinates(output)

            return SinfoResult(
                file_format=file_format,
                variables=variables,
                grid_coordinates=grid_coords,
                vertical_coordinates=vertical_coords,
                time_info=time_info,
            )
        except Exception as e:
            raise CDOParseError(
                message=f"Failed to parse sinfo output: {e}",
                raw_output=output[:500],
            ) from e

    def _parse_file_format(self, output: str) -> str:
        """Extract file format."""
        match = re.search(r"File format\s*:\s*(\S+)", output)
        if match:
            return match.group(1)
        return "Unknown"

    def _parse_variables(self, output: str) -> list[DatasetVariable]:
        """Parse variable table."""
        variables: list[DatasetVariable] = []

        print(output)
        # Find variable section (between header and "Grid coordinates")
        var_section = re.search(
            r"-1 : Institut Source.*?(?=Grid coordinates|$)", output, re.DOTALL
        )

        if not var_section:
            return variables

        lines = var_section.group(0).split("\n")[1:]  # Skip header

        for line in lines:
            line = line.strip()
            if not line or ":" not in line:
                continue

            # Parse: var_id : institut source table_code steptype levels num points num2 dtype : param_id
            parts = line.split(":")
            if len(parts) < 3:
                continue

            try:
                var_id = int(parts[0].strip())
                fields = parts[1].strip().split()

                # Parse param_id from third part (sinfo output does NOT include variable names)
                # Format: "param_id" only (e.g., "167")
                param_id_str = parts[2].strip()
                param_id = int(param_id_str) if param_id_str else -1

                if len(fields) >= 9:
                    variables.append(
                        DatasetVariable(
                            var_id=var_id,
                            institut=fields[0],
                            source=fields[1],
                            table_code=fields[2],
                            steptype=fields[3],
                            levels=int(fields[4]),
                            num=int(fields[5]),
                            points=int(fields[6]),
                            num2=int(fields[7]),
                            dtype=fields[8],
                            param_id=param_id,
                            name=None,  # sinfo doesn't provide variable names
                        )
                    )
            except (ValueError, IndexError):
                continue

        return variables

    def _parse_grid_coordinates(self, output: str) -> list[GridCoordinates]:
        """Parse grid coordinates section."""
        grids: list[GridCoordinates] = []

        # Find Grid coordinates section
        grid_section = re.search(
            r"Grid coordinates\s*:(.+?)(?=Vertical coordinates|Time coordinate|$)",
            output,
            re.DOTALL,
        )

        if not grid_section:
            return grids

        content = grid_section.group(1)

        # Parse each grid entry
        for grid_match in re.finditer(
            r"(\d+)\s*:\s*(\w+)\s*:.*?points=(\d+)\s*\((\d+)x(\d+)\)", content
        ):
            grid_id = int(grid_match.group(1))
            gridtype = grid_match.group(2)
            points = int(grid_match.group(3))
            xsize = int(grid_match.group(4))
            ysize = int(grid_match.group(5))

            grid = GridCoordinates(
                grid_id=grid_id,
                gridtype=gridtype,
                points=points,
                xsize=xsize,
                ysize=ysize,
            )

            # Parse longitude info
            lon_match = re.search(
                r"longitude\s*:\s*([\d.]+)\s+to\s+([\d.]+)\s+by\s+([\d.]+)\s+\[([^\]]+)\]",
                content[grid_match.end() :],
            )
            if lon_match:
                grid.longitude_start = float(lon_match.group(1))
                grid.longitude_end = float(lon_match.group(2))
                grid.longitude_inc = float(lon_match.group(3))
                grid.longitude_units = lon_match.group(4)

            # Parse latitude info
            lat_match = re.search(
                r"latitude\s*:\s*([\d.]+)\s+to\s+([\d.]+)\s+by\s+([\d.]+)\s+\[([^\]]+)\]",
                content[grid_match.end() :],
            )
            if lat_match:
                grid.latitude_start = float(lat_match.group(1))
                grid.latitude_end = float(lat_match.group(2))
                grid.latitude_inc = float(lat_match.group(3))
                grid.latitude_units = lat_match.group(4)

            grids.append(grid)

        return grids

    def _parse_vertical_coordinates(self, output: str) -> list[VerticalCoordinates]:
        """Parse vertical coordinates section."""
        verticals: list[VerticalCoordinates] = []

        # Find Vertical coordinates section
        vert_section = re.search(
            r"Vertical coordinates\s*:(.+?)(?=Time coordinate|$)", output, re.DOTALL
        )

        if not vert_section:
            return verticals

        content = vert_section.group(1)

        # Parse each vertical coordinate entry
        for vert_match in re.finditer(r"(\d+)\s*:\s*(\w+)\s*:.*?levels=(\d+)", content):
            zaxis_id = int(vert_match.group(1))
            zaxistype = vert_match.group(2)
            levels = int(vert_match.group(3))

            verticals.append(
                VerticalCoordinates(
                    zaxis_id=zaxis_id,
                    zaxistype=zaxistype,
                    levels=levels,
                )
            )

        return verticals

    def _parse_time_coordinates(self, output: str) -> TimeInfo:
        """Parse time coordinate section."""
        # Find Time coordinate section
        time_section = re.search(
            r"Time coordinate\s*:(.+?)(?=cdo\s+sinfo:|$)", output, re.DOTALL
        )

        if not time_section:
            raise CDOParseError(
                message="Time coordinate section not found",
                raw_output=output[:500],
            )

        content = time_section.group(1)

        # Parse number of steps
        steps_match = re.search(r"time\s*:\s*(\d+)\s+steps?", content)
        ntime = int(steps_match.group(1)) if steps_match else 0

        # Parse RefTime, Units, Calendar
        ref_match = re.search(r"RefTime\s*=\s*([^\s]+\s+[^\s]+)", content)
        units_match = re.search(r"Units\s*=\s*(\w+)", content)
        cal_match = re.search(r"Calendar\s*=\s*(\w+)", content)

        ref_time = ref_match.group(1) if ref_match else ""
        units = units_match.group(1) if units_match else ""
        calendar = cal_match.group(1) if cal_match else "standard"

        # Parse first and last timesteps (exclude RefTime line)
        lines_without_reftime = [
            line for line in content.split("\n") if "RefTime" not in line
        ]
        timesteps = []
        for line in lines_without_reftime:
            matches = re.findall(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", line)
            timesteps.extend(matches)

        first_timestep = timesteps[0] if timesteps else None
        last_timestep = timesteps[-1] if timesteps else None

        return TimeInfo(
            ntime=ntime,
            ref_time=ref_time,
            units=units,
            calendar=calendar,
            first_timestep=first_timestep,
            last_timestep=last_timestep,
        )


class InfoParser(CDOParser[InfoResult]):
    """
    Parser for info command output.

    Parses timestep-by-timestep statistics.
    """

    def parse(self, output: str) -> InfoResult:
        """
        Parse info output.

        Args:
            output: Raw output from CDO info command.

        Returns:
            InfoResult containing timestep information.

        Raises:
            CDOParseError: If parsing fails.
        """
        timesteps: list[TimestepInfo] = []

        # Parse each timestep line
        for line in output.split("\n"):
            line = line.strip()
            if not line or ":" not in line:
                continue

            # Skip header lines - check for various header formats
            # Header line starts with ':' and contains column names
            # We need to check this BEFORE checking if line starts with digit
            if "Date" in line and "Time" in line:
                continue

            # Try to parse as timestep line - must start with number after stripping
            if not line[0].isdigit():
                continue

            try:
                # Parse: timestep : date time level gridsize miss : min mean max : param_id
                parts = line.split(" :")
                if len(parts) < 4:
                    continue

                # First part must be a valid timestep number
                timestep_str = parts[0].strip()
                if not timestep_str.isdigit():
                    continue
                timestep = int(timestep_str)

                # Date and time
                datetime_parts = parts[1].strip().split()
                if len(datetime_parts) < 5:  # Need date, time, level, gridsize, miss
                    continue
                date = datetime_parts[0]
                time = datetime_parts[1]
                level = int(datetime_parts[2])
                gridsize = int(datetime_parts[3])
                miss = int(datetime_parts[4])

                # Statistics
                stats = parts[2].strip().split()
                if len(stats) < 3:
                    continue
                minimum = float(stats[0])
                mean = float(stats[1])
                maximum = float(stats[2])

                # Parameter ID
                param_id = int(parts[3].strip())

                timesteps.append(
                    TimestepInfo(
                        timestep=timestep,
                        date=date,
                        time=time,
                        level=level,
                        gridsize=gridsize,
                        miss=miss,
                        minimum=minimum,
                        mean=mean,
                        maximum=maximum,
                        param_id=param_id,
                    )
                )
            except (ValueError, IndexError):
                continue

        if not timesteps:
            raise CDOParseError(
                message="No timesteps found in info output",
                raw_output=output[:500],
            )

        return InfoResult(timesteps=timesteps)


class VlistParser(CDOParser[VlistResult]):
    """
    Parser for vlist command output.

    Parses complete variable list with metadata.
    """

    def parse(self, output: str) -> VlistResult:
        """
        Parse vlist output.

        Args:
            output: Raw output from CDO vlist command.

        Returns:
            VlistResult containing variable information.

        Raises:
            CDOParseError: If parsing fails.
        """
        try:
            # Parse header
            vlist_id_match = re.search(r"vlistID\s+(\d+)", output)
            vlist_id = int(vlist_id_match.group(1)) if vlist_id_match else 0

            nvars = self._extract_field(output, "nvars")
            ngrids = self._extract_field(output, "ngrids")
            nzaxis = self._extract_field(output, "nzaxis")
            nsubtypes = self._extract_field(output, "nsubtypes")
            taxis_id = self._extract_field(output, "taxisID")
            inst_id = self._extract_field(output, "instID")
            model_id = self._extract_field(output, "modelID")
            table_id = self._extract_field(output, "tableID")

            # Parse variables
            variables = self._parse_variables(output)

            # Validate that we got at least minimal valid output
            if nvars == 0 and not vlist_id_match:
                raise CDOParseError(
                    message="Invalid vlist output: no vlistID or variables found",
                    raw_output=output[:500],
                )

            return VlistResult(
                vlist_id=vlist_id,
                nvars=nvars,
                ngrids=ngrids,
                nzaxis=nzaxis,
                nsubtypes=nsubtypes,
                taxis_id=taxis_id,
                inst_id=inst_id,
                model_id=model_id,
                table_id=table_id,
                variables=variables,
            )
        except Exception as e:
            raise CDOParseError(
                message=f"Failed to parse vlist output: {e}",
                raw_output=output[:500],
            ) from e

    def _extract_field(self, output: str, field_name: str) -> int:
        """Extract integer field value."""
        match = re.search(rf"{field_name}\s*:\s*(-?\d+)", output)
        return int(match.group(1)) if match else 0

    def _parse_variables(self, output: str) -> list[VariableInfo]:
        """Parse variable definitions."""
        variables: list[VariableInfo] = []

        # Find variable definition section
        var_section = re.search(
            r"varID param.*?(?=varID\s+levID|varID\s+size|$)", output, re.DOTALL
        )

        if not var_section:
            return variables

        lines = var_section.group(0).split("\n")[1:]  # Skip header

        for line in lines:
            line = line.strip()
            if not line or line.startswith("varID") or line.startswith("cdo"):
                continue

            fields = line.split()
            if len(fields) < 10:
                continue

            try:
                var_id = int(fields[0])
                param = int(fields[1])
                grid_id = int(fields[2])
                zaxis_id = int(fields[3])
                stype_id = int(fields[4])
                tstep_type = int(fields[5])
                flag = int(fields[6])
                name = fields[7]

                # longname and units might be concatenated, extract carefully
                longname = " ".join(fields[8:-1]) if len(fields) > 10 else fields[8]
                units = fields[-1] if len(fields) > 9 else None

                # Handle units in brackets
                if longname and "[" in longname:
                    parts = longname.rsplit("[", 1)
                    longname = parts[0].strip()
                    units = parts[1].rstrip("]").strip() if len(parts) > 1 else units
                elif units and units.startswith("[") and units.endswith("]"):
                    units = units[1:-1]

                variables.append(
                    VariableInfo(
                        var_id=var_id,
                        param=param,
                        grid_id=grid_id,
                        zaxis_id=zaxis_id,
                        stype_id=stype_id,
                        tstep_type=tstep_type,
                        flag=flag,
                        name=name,
                        longname=longname if longname != name else None,
                        units=units,
                    )
                )
            except (ValueError, IndexError):
                continue

        return variables


class PartabParser(CDOParser[PartabResult]):
    """
    Parser for partab/codetab command output.

    Parses parameter table entries.
    """

    def parse(self, output: str) -> PartabResult:
        """
        Parse partab output.

        Args:
            output: Raw output from CDO partab command.

        Returns:
            PartabResult containing parameter information.

        Raises:
            CDOParseError: If parsing fails.
        """

        parameters: list[PartabInfo] = []
        table_name = None

        # Extract table name if present
        table_match = re.search(r"Parameter table:\s*(.+)", output)
        if table_match:
            table_name = table_match.group(1).strip()

        # Check if this is Fortran namelist format
        if "&parameter" in output.lower():
            parameters = self._parse_fortran_namelist(output)
        else:
            # Parse table format
            lines = output.strip().split("\n")

            for line in lines:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("cdo"):
                    continue

                # Skip header lines
                if "code" in line.lower() and "name" in line.lower():
                    continue
                # Skip the "Parameter table: NAME" line itself (don't parse it as data)
                if line.startswith("Parameter") and "table:" in line:
                    continue

                # Try to parse the line
                param_info = self._parse_parameter_line(line)
                if param_info:
                    parameters.append(param_info)

        if not parameters:
            raise CDOParseError(
                message="No parameters found in partab output",
                raw_output=output[:500],
            )

        return PartabResult(
            parameters=parameters,
            table_name=table_name,
        )

    def _parse_fortran_namelist(self, output: str) -> list[PartabInfo]:
        """
        Parse Fortran namelist format from CDO partab output.

        Format example:
        &parameter
          code = 1
          name = 'temperature'
          units = 'K'
          long_name = 'Temperature'
          datatype = 'r4'
        /

        Args:
            output: Raw CDO output containing Fortran namelists.

        Returns:
            List of PartabInfo objects.
        """

        parameters: list[PartabInfo] = []

        # Split by namelist blocks (between & and /)
        blocks = re.split(r"&parameter", output, flags=re.IGNORECASE)

        for block in blocks[1:]:  # Skip first empty block before first &parameter
            # Find end of this namelist (/)
            end_match = re.search(r"/", block)
            if end_match:
                block = block[: end_match.start()]

            # Extract fields using regex
            code_match = re.search(
                r'code\s*=\s*["\']?([^"\',\n]+)["\']?', block, re.IGNORECASE
            )
            name_match = re.search(
                r'name\s*=\s*["\']?([^"\',\n]+?)["\']?(?:\s|$)', block, re.IGNORECASE
            )
            units_match = re.search(
                r'units\s*=\s*["\']([^"\']+)["\']', block, re.IGNORECASE
            )
            longname_match = re.search(
                r'long_name\s*=\s*["\']([^"\']+)["\']', block, re.IGNORECASE
            )

            if name_match:
                name = name_match.group(1).strip()
                # Use code if available, otherwise use name as code
                code = code_match.group(1).strip() if code_match else name
                units = units_match.group(1).strip() if units_match else None
                longname = longname_match.group(1).strip() if longname_match else None

                parameters.append(
                    PartabInfo(
                        code=code,
                        name=name,
                        units=units,
                        description=None,
                        longname=longname,
                        raw=block.strip(),
                    )
                )

        return parameters

    def _parse_parameter_line(self, line: str) -> PartabInfo | None:
        """
        Parse a single parameter line.

        Supports multiple formats:
        - Pipe-separated: code | name | units | description
        - Tab-separated: code\tname\tunits\tdescription
        - Space-separated: code name units [description...]

        Args:
            line: Line to parse.

        Returns:
            PartabInfo if successfully parsed, None otherwise.
        """

        # Try pipe-separated format first
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2:
                return PartabInfo(
                    code=parts[0],
                    name=parts[1],
                    units=parts[2] if len(parts) > 2 else None,
                    description=parts[3] if len(parts) > 3 else None,
                    longname=parts[4] if len(parts) > 4 else None,
                    raw=line,
                )

        # Try tab-separated format
        if "\t" in line:
            parts = [p.strip() for p in line.split("\t") if p.strip()]
            if len(parts) >= 2:
                return PartabInfo(
                    code=parts[0],
                    name=parts[1],
                    units=parts[2] if len(parts) > 2 else None,
                    description=" ".join(parts[3:]) if len(parts) > 3 else None,
                    raw=line,
                )

        # Try space-separated format
        parts = line.split()
        if len(parts) >= 2:
            # First part should be code (numeric or string)
            code = parts[0]
            name = parts[1]
            units = parts[2] if len(parts) > 2 else None
            description = " ".join(parts[3:]) if len(parts) > 3 else None

            return PartabInfo(
                code=code,
                name=name,
                units=units,
                description=description,
                raw=line,
            )

        return None
