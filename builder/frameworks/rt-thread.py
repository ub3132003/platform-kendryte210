import os
import sys
from os.path import isdir, join

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()

FRAMEWORK_DIR = env.PioPlatform().get_package_dir("framework-rt-thread")
assert FRAMEWORK_DIR and isdir(FRAMEWORK_DIR)
os.chdir(FRAMEWORK_DIR+"\\bsp"+"\\k210")
sys.path.append(FRAMEWORK_DIR+"\\bsp"+"\\k210")
sys.path.append(FRAMEWORK_DIR+"\\tools")
import rtconfig
from rtconfig import RTT_ROOT

sys.path = sys.path + [os.path.join(RTT_ROOT, 'tools')]
from building import *

DefaultEnvironment(tools=[])
env = Environment(tools = ['mingw'],
    AS = rtconfig.AS, ASFLAGS = rtconfig.AFLAGS,
    CC = rtconfig.CC, CCFLAGS = rtconfig.CFLAGS,
    CXX = rtconfig.CXX, CXXFLAGS = rtconfig.CXXFLAGS,
    AR = rtconfig.AR, ARFLAGS = '-rc',
    LINK = rtconfig.LINK, LINKFLAGS = rtconfig.LFLAGS)
env.PrependENVPath('PATH', rtconfig.EXEC_PATH)
env['ASCOM'] = env['ASPPCOM']

Export('RTT_ROOT')
Export('rtconfig')

# prepare building environment
objs = PrepareBuilding(env, RTT_ROOT, has_libcpu = False)

stack_size = 4096
stack_lds = open('link_stacksize.lds', 'w')
if GetDepend('__STACKSIZE__'): stack_size = GetDepend('__STACKSIZE__')
stack_lds.write('__STACKSIZE__ = %d;' % stack_size)
stack_lds.close()

# make a building
DoBuilding(TARGET, objs)


env.SConscript("_bare.py", exports="env")

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
    env.Replace(LDSCRIPT_PATH=join(FRAMEWORK_DIR, "bsp","k210", "link.lds"))

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