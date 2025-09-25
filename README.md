# x-ray
This project aims to create tools for MongoDB analysis and diagnosis. So far 2 modules are built:
- Health check module.
- Log analysis module (Under construction).

## 1 Compatibility Matrix
|  Replica Set  | Sharded Cluster | Standalone |
| :-----------: | :-------------: | :--------: |
| >=4.2 &check; |  >=4.2 &check;  |  &cross;   |

Older versions are not tested.

## 2 Dependencies
The tool is tested with `Python 3.9.22`.
```bash
make init # if it's the first time you build the project
make
```
The compiled executable is in the folder `./dist/`.

For developers the `make init` will be enough to prepare the environment so you can run this tool in the IDE.

## 3 Using the Tool
```bash
x-ray [-h] [-q] [-c CONFIG] {healthcheck,hc,log}
```
|     Argument     |                                          Description                                           |        Default         |
| ---------------- | ---------------------------------------------------------------------------------------------- | :--------------------: |
| `-q`, `--quiet`  | Quiet mode.                                                                                    |        `false`         |
| `-h`, `--help`   | Show the help message and exit.                                                                |          n/a           |
| `-c`, `--config` | Path to configuration file.                                                                    | Built-in `config.json` |
| `command`        | Command to run. Include:<br/>- `healthcheck` or `hc`: Health check.<br/>- `log`: Log analysis. |          None          |

Besides, you can use environment variables to control some behaviors:
- `ENV=development` For developing. It will change the following behaviors:
  - Formatted the output JSON for for easier reading.
  - The output will not create a new folder for each run but overwrite the same files.
- `LOG_LEVEL`: Can be `DEBUG`, `ERROR` or `INFO` (default).
- 
### 3.1 Health Check Component
#### 3.1.1 Examples
```bash
./x-ray healthcheck localhost:27017 # Scan the cluster with default settings.
./x-ray hc localhost:27017 --output ./output/ # Specify output folder.
./x-ray hc localhost:27017 --config ./config.json # Use your own configuration.
```

#### 3.1.2 Full Arguments
```bash
x-ray healthcheck [-h] [-s CHECKSET] [-o OUTPUT] [-f {markdown,html}] [uri]
```
|      Argument      |                 Description                 |  Default  |
| ------------------ | ------------------------------------------- | :-------: |
| `-s`, `--checkset` | Checkset to run.                            | `default` |
| `-o`, `--output`   | Output folder path.                         | `output/` |
| `-f`, `--format`   | Output format. Can be `markdown` or `html`. |  `html`   |
| `uri`              | MongoDB database URI.                       |   None    |

For security reasons you may not want to include credentials in the command. There are 2 options:
- If the URI is not provided, user will be asked to input one.
- If URI is provided but not username/password, user will also be asked to input them.

#### 3.1.3 More Info
Refer to the wiki for more details.
- [Customize the thresholds](https://github.com/zhangyaoxing/x-ray/wiki/Health-Check-Configuration)
- [Database permissions](https://github.com/zhangyaoxing/x-ray/wiki/Health-Check-Database-Permissions)
- [Output](https://github.com/zhangyaoxing/x-ray/wiki/Health-Check-Output)
- [Customize the output](https://github.com/zhangyaoxing/x-ray/wiki/Health-Check-Output-Template)

### 3.2 Log Analysis Component
#### 3.2.1 Examples
```bash
# Full analysis
./x-ray log mongodb.log
# For large logs, analyze a random 10% logs
./x-ray log -r 0.1 mongodb.log
```

#### 3.2.2 Full Arguments
```bash
x-ray log [-h] [-s CHECKSET] [-o OUTPUT] [-f {markdown,html}] [log_file]
```
|      Argument      |                    Description                    |  Default  |
| ------------------ | ------------------------------------------------- | :-------: |
| `-s`, `--checkset` | Checkset to run.                                  | `default` |
| `-o`, `--output`   | Output folder path.                               | `output/` |
| `-f`, `--format`   | Output format. Can be `markdown` or `html`.       |  `html`   |
| `-r`, `--rate`     | Sample rate. Only analyze a subset of logs.       |    `1`    |
| `--top`            | When analyzing the slow queries, only list top N. |   `10`    |