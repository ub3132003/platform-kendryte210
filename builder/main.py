import sys
from os.path import join

from SCons.Script import (ARGUMENTS, COMMAND_LINE_TARGETS, AlwaysBuild,
                          Builder, Default, DefaultEnvironment)

join(r'C:\Users\sun\.platformio\packages\toolchain-riscv-none-gcc\riscv-embedded-gcc\8.2.0-2.2-20190521-0004\bin')
#sys.path.append(FRAMEWORK_DIR+"\\bsp"+"\\k210")
join(r'C:\Users\sun\.platformio\packages\platform-rt-thread\bsp\k210')
sys.path.append(r'C:\Users\sun\.platformio\packages\platform-rt-thread\bsp\k210')
env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
PREFIX  = 'riscv-none-embed-'
env.Replace(
    # toolchains
    
    CC      = PREFIX + 'gcc',
    AR      = PREFIX + 'ar',
    AS      = PREFIX + 'gcc',
    GDB     = PREFIX + 'gdb',
    CXX     = PREFIX + 'g++',
    OBJCOPY = PREFIX + 'objcopy',
    RANLIB  = PREFIX + 'ranlib',
    SIZETOOL= PREFIX + "size",
    ARFLAGS=["rcs"],

    SIZEPRINTCMD='$SIZETOOL -d $SOURCES',

    PROGSUFFIX=".elf"
)

# Allow user to override via pre:script
if env.get("PROGNAME", "program") == "program":
    env.Replace(PROGNAME="firmware")

env.Append(
    BUILDERS=dict(
        ElfToBin=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-O",
                "binary",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET"),
            suffix=".bin"
        ),
        ElfToHex=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-O",
                "srec",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET"),
            suffix=".hex"
        )
    )
)

if not env.get("PIOFRAMEWORK"):
    env.SConscript("frameworks/_bare.py", exports="env")

#
# Target: Build executable and linkable firmware
#

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_elf = join("$BUILD_DIR", "${PROGNAME}.elf")
    target_firm = join("$BUILD_DIR", "${PROGNAME}.bin")
else:
    target_elf = env.BuildProgram()
    target_firm = env.ElfToBin(join("$BUILD_DIR", "${PROGNAME}"), target_elf)

AlwaysBuild(env.Alias("nobuild", target_firm))
target_buildprog = env.Alias("buildprog", target_firm, target_firm)

#
# Target: Print binary size
#

target_size = env.Alias(
    "size", target_elf,
    env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE"))
AlwaysBuild(target_size)

#
# Target: Upload by default .bin file
#

upload_protocol = env.subst("$UPLOAD_PROTOCOL")
debug_tools = board.get("debug.tools", {})
upload_source = target_firm
upload_actions = []

if upload_protocol == "kflash":

    if not env.subst("$UPLOAD_PORT") and board.get("upload.burn_tool") == "goE" : #use kflash autoselect port
        port_str = "DEFAULT"
    else:
        port_str = "$UPLOAD_PORT"

    env.Replace(
        UPLOADER=join(platform.get_package_dir("tool-kflash-kendryte210") or "", "kflash.py"),
        UPLOADERFLAGS=[
            # "-n",
            "-p", port_str,
            "-b", "$UPLOAD_SPEED",
            "-B", board.get("upload.burn_tool")
        ],

        UPLOADCMD='"$PYTHONEXE" "$UPLOADER" $UPLOADERFLAGS $SOURCE',
    )
    upload_actions = [
        env.VerboseAction(env.AutodetectUploadPort, "Looking for upload port..."),
        env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")
    ]

# TODO: openocd debug upload
elif upload_protocol in debug_tools:
    openocd_args = [
        "-d%d" % (2 if int(ARGUMENTS.get("PIOVERBOSE", 0)) else 1)
    ]
    openocd_args.extend(
        debug_tools.get(upload_protocol).get("server").get("arguments", []))
    openocd_args.extend([
        "-c", "program {$SOURCE} %s verify reset; shutdown;" %
        board.get("upload.offset_address", "")
    ])
    openocd_args = [
        f.replace("$PACKAGE_DIR",
                  platform.get_package_dir("tool-openocd-kendryte") or "")
        for f in openocd_args
    ]
    env.Replace(
        UPLOADER="openocd",
        UPLOADERFLAGS=openocd_args,
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS")
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

# custom upload tool
elif upload_protocol == "custom":
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

else:
    sys.stderr.write("Warning! Unknown upload protocol %s\n" % upload_protocol)

AlwaysBuild(env.Alias("upload", upload_source, upload_actions))

#
# Setup default targets
#

Default([target_buildprog, target_size])
