#!/usr/bin/env python3

import click
import yaml
from myhdl import *
import sys
import os.path
import shutil
from .hw.hw_util import *
from .hw.test_z01 import test_z01
from .sw.assembler.ASM import ASM
from .sw.vmtranslator.VMTranslate import VMTranslate
from .sw.vmtranslator.Code import Code as VMCode
from .util.toMIF import toMIF
from .util.programFPGA import programCDF, programROM
from .util.genImg import memTopgm
from .util.debuglst import debugLst
from .util.debugStack import debugStack


def getName(nasm):
    return nasm.split(".")[0]


def clearDir(d):
    shutil.rmtree(os.path.dirname(d))


def createDir(d):
    dir = os.path.dirname(d)
    if os.path.exists(dir) is False:
        os.makedirs(dir)


def vm_to_nasm(vm, nasm):
    createDir(nasm)
    fNasm = open(nasm, "w")
    v = VMTranslate(vm, fNasm)
    v.run()


def vm_test(vm, ram, test, time=100000):
    nasm = os.path.join("nasm", vm + ".nasm")
    vm_to_nasm(vm, nasm)
    return nasm_test(nasm, ram, test, time)


def nasm_test(nasm, ram, test, time=1000):
    name = getName(nasm)
    hack = name + ".hack"
    nasm_to_hack(nasm, hack)
    rom = rom_init_from_hack(hack)

    run = proc_run(name, rom, ram, time)

    return True if ram_test(test, run["ram"]) == 0 else False


def nasm_to_hack(nasm, hack, mif=False):
    print(" 1/1 gerando novos arquivos .hack")
    print(" destine: {}".format(hack))

    fNasm = open(nasm, "r")
    fHack = open(hack, "w")
    asm = ASM(fNasm, fHack)
    asm.run()
    fHack.close()

    if mif:
        toMIF(hack, getName(hack) + ".mif")


def proc_run(name, rom, ram, time, dump=True, img=True):
    cpu = test_z01(name, rom, ram, time)
    run = cpu.run()
    if dump:
        cpu.dump()

    if img:
        memTopgm(ram, name)

    return run


# ------------------------- #


@click.group()
@click.option("--debug", "-b", is_flag=True, help="Enables verbose mode.")
@click.pass_context
def cli(ctx, debug):
    pass


# ------------------------- #


@click.group()
def gui():
    pass


@gui.command()
def nasm():
    dir = os.path.join(os.path.dirname(__file__), "sw", "simulator")
    os.chdir(dir)
    from bits.sw.simulator.main import init_simulator_gui

    init_simulator_gui()


@gui.command()
@click.argument("lstfile")
@click.option("--ram", is_flag=True, help="Prints ram table")
def lst(ram, lstfile):
    debugLst(lstfile, ram)


@gui.command()
@click.argument("lstfile")
def stack(lstfile):
    debugStack(lstfile)


# ------------------------- #


@cli.command()
@click.option("--mif", is_flag=True, help="also generates mif file")
@click.argument("nasm")
def assembly(nasm, mif):
    hack = getName(nasm) + ".hack"
    click.echo("Syncing")
    nasm_to_hack(nasm, hack, mif)


# ------------------------- #


@click.group()
def program():
    pass


@program.command()
@click.argument("cdf")
def fpga(cdf):
    if programCDF(cdf):
        print("FPGA NÃ̀O PROGRAMADA!")


@program.command()
@click.argument("fname")
def rom(fname):
    name, type = fname.split(".")

    if type == "nasm":
        nasm_to_hack(fname, name + ".hack", True)
    elif type == "hack":
        toMIF(fname, name + ".mif")
    elif type == "mif":
        pass
    else:
        print("Erro: pass an .nasm, .hack or .mif file")

    programROM(name + ".mif")


# ------------------------- #


cli.add_command(gui)
cli.add_command(program)

if __name__ == "__main__":
    cli()
