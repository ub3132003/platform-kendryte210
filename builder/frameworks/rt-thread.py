

from os.path import isdir, join

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()

FRAMEWORK_DIR = env.PioPlatform().get_package_dir("framework-rt-thread")
assert FRAMEWORK_DIR and isdir(FRAMEWORK_DIR)

env.SConscript("rtconfig.py", exports="env")

env.Append(


    CPPDEFINES = [
        ("NNCASE_TARGET", "k210"),
        "TCB_SPAN_NO_EXCEPTIONS",
        "TCB_SPAN_NO_CONTRACT_CHECKING"
    ],

    LINKFLAGS = [
        "-Wl,--start-group",
        "-lc",
        "-lgcc",
        "-lm",
        "-Wl,--end-group"
    ],

    CPPPATH = [
        join(FRAMEWORK_DIR,  "bsp","k210"),
        join(FRAMEWORK_DIR, "bsp","k210", "bsp", "include"),
        join(FRAMEWORK_DIR, "bsp","k210", "drivers"),
        join(FRAMEWORK_DIR, "bsp","k210", "drivers", "include"),
    ],

    LIBPATH = [

    ],

    LIBS = [
        "c", "gcc", "m", "stdc++"
    ]

)

if not env.BoardConfig().get("build.ldscript", ""):
    env.Replace(LDSCRIPT_PATH=join(FRAMEWORK_DIR, "lds", "kendryte.ld"))

#
# Target: Build Core Library
#

libs = [
    env.BuildLibrary(
        join("$BUILD_DIR", "sdk-bsp"),
        join(FRAMEWORK_DIR, "lib", "bsp")),

    env.BuildLibrary(
        join("$BUILD_DIR", "sdk-drivers"),
        join(FRAMEWORK_DIR, "lib", "drivers")),

    env.BuildLibrary(
        join("$BUILD_DIR", "sdk-freertos"),
        join(FRAMEWORK_DIR, "lib", "freertos")),

    env.BuildLibrary(
        join("$BUILD_DIR", "nncase"),
        join(FRAMEWORK_DIR, "lib", "nncase")),
]

env.Prepend(LIBS=libs)