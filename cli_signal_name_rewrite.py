import collections
import glob
import re
import sys
import typing

import yaml

""" Set this to True to preview what the program does to the IRDB
"""
_dry_run = False


def _open_single_file(file_name: str, pa_cb, dry_run: bool = False):
    write_lines = []
    content_changed = False
    with open(file_name, 'r') as osf_fd:
        for line in osf_fd.readlines():
            line = line.strip('\n')
            # ignore comments
            if line.startswith('#'):
                write_lines.append(line)
                continue
            if ':' in line:
                colon = line.index(':')
                osf_key = line[:colon].strip()
                osf_val = line[colon + 1:].strip()

                # if replace is None, don't write line
                if (osf_replace := pa_cb(osf_key, osf_val)) and osf_replace != osf_val:
                    content_changed = True
                    write_lines.append(f'{osf_key}: {osf_replace}')
                else:
                    write_lines.append(line)
    if content_changed:
        # make sure the file ends with a new-line
        if write_lines[-1] != '':
            write_lines.append('')
        if dry_run:
            return
        with open(file_name, 'w') as osf_fd:
            osf_fd.write('\n'.join(write_lines))


def _find_key_from_map(
        value: str,
        replacement_map: dict[str, list[str | re.Pattern]],
        normalize: bool = False
) -> typing.Optional[str]:
    if normalize:
        value = value.strip().lower().replace(' ', '').replace('_', '')
    for replacement_map_key, replacement_map_vals in replacement_map.items():
        for replacement_map_val in replacement_map_vals:
            if isinstance(replacement_map_val, str):
                if replacement_map_val == value:
                    return replacement_map_key
            if isinstance(replacement_map_val, re.Pattern):
                if replacement_map_val.match(value):
                    return replacement_map_key
    return None


def _get_assert_type(
        dic: dict,
        dict_key: str,
        typ: type,
        default: object = None,
        allow_empty: bool = False
) -> typing.Any:
    assert_val = dic.get(dict_key) or default
    if assert_val is not None and not isinstance(assert_val, typ):
        raise RuntimeError(f"{dict_key} has to be of type {typ} but was {type(assert_val)}: {val}")
    if assert_val is None and not allow_empty:
        raise RuntimeError(f"{dict_key} has to be set")
    return assert_val


def _get_re_or_str(
        what: str,
        normalize: bool = False
) -> str | re.Pattern:
    if not what.startswith("/") or not what.endswith("/"):
        if normalize:
            what = what.strip().lower()
        return what
    return re.compile(what[1:-1])


def _run_action_replace(
        replace_map: dict,
        action_replace_key: str,
        action_replace_val: str
) -> str:
    for replacer in replace_map[action_replace_key]:
        replacer_find = replacer["find"]
        replacer_replace: str = replacer["replace"]
        old_val = action_replace_val  # used to check if we changed something
        if isinstance(replacer_find, re.Pattern):
            action_replace_val = replacer_replace.join(replacer_find.split(action_replace_val))
        else:
            action_replace_val = action_replace_val.replace(replacer_find, replacer_replace)
        if _dry_run and old_val != action_replace_val:
            print(f"    [dry-run/replacer] replaced {replacer_find} with {replacer_replace}")
    return action_replace_val


def _run_action_rewrite(
        rewrite_map: dict,
        action_rewrite_val: str
) -> str:
    if (new_callback_value := _find_key_from_map(
            value=action_rewrite_val,
            replacement_map=rewrite_map,
            normalize=True
    )) and new_callback_value != action_rewrite_val:
        if _dry_run:
            print("    [dry-run/rewrite] replaced", action_rewrite_val, "with", new_callback_value)
        action_rewrite_val = new_callback_value
    return action_rewrite_val


def main():
    with open("flipper_signal_rewrites.yaml", "r") as fd:
        data = yaml.safe_load(fd)
    if not isinstance(data, list):
        raise ValueError("YAML should contain a list at the top-level.")

    args = sys.argv[1:] or ["rewrite"]

    is_action_rewrite = "rewrite" in args[0].lower()
    is_action_replace = "replace" in args[0].lower()

    # a list that contains all file paths which have been processed
    processed_files: set[str] = set()

    for rewrite_dict in data:
        if not isinstance(rewrite_dict, dict):
            raise ValueError("list item should be a dict.")

        # allow to specify which types (TV, AC, ...) should be run
        name: str = _get_assert_type(rewrite_dict, "name", str, default='')
        if len(args) > 1 and name not in args[1:]:
            continue

        paths_exclude: list[str] = _get_assert_type(rewrite_dict, "exclude", list, allow_empty=True)
        paths_exclude_list = []
        if paths_exclude:
            paths_exclude_list = [file_name for z in paths_exclude for file_name in glob.glob(z, recursive=True)]

        # transform list to key-str/regex dict
        rewrite: dict = _get_assert_type(rewrite_dict, "rewrite", dict, allow_empty=True)
        rewrite_replacement_map: dict[str, list[re.Pattern | str]] = collections.defaultdict(list)
        if is_action_rewrite and rewrite:
            for k, vals in rewrite.items():
                for val in vals:
                    if not isinstance(val, str):
                        raise ValueError(f"invalid type: {type(val)} - should be of type string: {val}")
                    rewrite_replacement_map[k].append(_get_re_or_str(val, normalize=True))

        # replace in value
        replace: list[dict] = _get_assert_type(rewrite_dict, "replace", list, allow_empty=True)
        replaces = collections.defaultdict(list)
        if is_action_replace and replace:
            for replace_dict in replace:
                find: str = _get_assert_type(replace_dict, "find", str)
                replace: str = _get_assert_type(replace_dict, "replace", str)
                keys: list[str] = _get_assert_type(replace_dict, "keys", list)

                find_instance = _get_re_or_str(find, normalize=False)
                for key in keys:
                    replaces[key.lower().strip()].append({"find": find_instance, "replace": replace})

        ignore_previous: bool = _get_assert_type(rewrite_dict, "ignore-previous", bool, default=False)
        paths_include: list[str] = _get_assert_type(rewrite_dict, "include", list)

        for path in (file_name for z in paths_include for file_name in glob.glob(z, recursive=True)):
            if path in paths_exclude_list:
                continue

            print(f'[{name}] Processing "{path}" ...')

            # ignore files which have been processed earlier
            if not ignore_previous and path in processed_files:
                continue
            processed_files.update(path)

            def callback(callback_key: str, callback_val: str) -> str:
                callback_key = callback_key.lower().strip()

                # replace?
                if is_action_replace:
                    callback_val = _run_action_replace(
                        replace_map=replaces,
                        action_replace_key=callback_key,
                        action_replace_val=callback_val
                    )

                # rewrite
                if is_action_rewrite and callback_key == "name":
                    callback_val = _run_action_rewrite(
                        rewrite_map=rewrite_replacement_map,
                        action_rewrite_val=callback_val
                    )

                return callback_val

            _open_single_file(path, callback, dry_run=_dry_run)


if __name__ == '__main__':
    main()
