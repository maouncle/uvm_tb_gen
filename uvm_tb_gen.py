# !usr/bin/python
##
##-------------------------------------------------
##generate uvm tb , basically including 5 level structure. top/test/env/agent/seq/seqer/driver/monitor/interface, scb/refm/cov/assertion/seqlib
##project
##      +rtl
##      +doc
##      +dv
##          +tb
##          +env
##          +agent
##          +tests
##            +seqlib
##          +sim
##            +scripts
##this script is based on an open uvm_tb_gen.pl please contact  getwkg@163.com.
# ***********************************************************************
# *****   *********       Copyright (c) 2018
# ***********************************************************************
# PROJECT        :
# FILENAME       : uvm_tb_gen.py
# Author         : [dpc525@163.com]
# LAST MODIFIED  : 2018-03-24 16:06
# ***********************************************************************
# DESCRIPTION    :
# ***********************************************************************
# $Revision: $
# $Id: $
# ***********************************************************************
# --------------------------------------------------
import re
import sys
import os
import getopt


def usage():
    print
    "	********USAGE: python uvm_tb_gen.py -help/h (print this message)********\n"
    print
    "	this scritps support several input agent, output agent, agent with ral"
    print
    "	for the ral agent, support adapter for i2c/spi/apb/ahb,not support yet."
    print
    "	Any suggestion, please contact  dpc525@163.com"
    print
    "	python uvm_tb_gen.py -p project name -i list (input agent name)/active -o list (output agent name)/passive -r register agent with ral\n"
    print
    "	example 1: one input agent, one output agent,one ral agent:\n		python uvm_tb_gen.py -p uart -i uart -o localbus -r apb\n"
    print
    "	example 2: two input agent:\n 		                                python uvm_tb_gen.py -p uart -i uart localbus\n"
    print
    "	example 3: two input agent, one output agent,two ral agent:\n 		python uvm_tb_gen.py -p uart -i uart localbus -o outp -r apb ahb\n"
    print
    "	********************************************************************\n"


def tb_gen(argv):
    global project  # = "--undef--"
    global tbname  # = "--undef--"
    global envname  # = "--undef--"
    global agent_name  # = "--undef--"
    global agent_if  # = "--undef--"
    global agent_item  # = "--undef--"
    global agent_list

    mode = "irun"
    i_agt = []
    o_agt = []

    try:
        opts, args = getopt.getopt(argv, "p:i:i:o:runvcs", ["project", "agent"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            usage()
            sys.exit()

        elif opt in ("-p", "project"):
            project = arg
        elif opt in ("-i"):
            agent_name = arg
            i_agt.append(arg)
        elif opt in ("-o"):
            o_agt.append(arg)
        elif opt in ("-irun"):
            mode = "irun"
        elif opt in ("-vcs"):
            mode = "vcs"

    tbname = project
    envname = project + "_env"
    agent_list = i_agt + o_agt

    print
    "The project name is", project
    print
    "The agent name is", agent_name
    print
    "The simulator is ", mode
    print
    "The agent_list is ", agent_list
    print
    "\nParsing  Input Agent ...\n\n"
    print
    "Writing code to files"
    if os.path.exists(project + "/doc/") != True:
        os.makedirs(project + "/doc/")

    if os.path.exists(project + "/rtl/") != True:
        os.makedirs(project + "/rtl/")

    if os.path.exists(project + "/dv/env/") != True:
        os.makedirs(project + "/dv/env/")

    if os.path.exists(project + "/dv/tb/") != True:
        os.makedirs(project + "/dv/tb/")

    if os.path.exists(project + "/dv/sim/") != True:
        os.makedirs(project + "/dv/sim/")
    # os.makedirs(project+"/dv/tests/")
    if os.path.exists(project + "/dv/tests/test_seq") != True:
        os.makedirs(project + "/dv/tests/test_seq")

    template_type = "act"
    for agt in i_agt:
        if os.path.exists(project + "/dv/agent/" + agt) != True:
            os.makedirs(project + "/dv/agent/" + agt)
        # create the agent files
        agent_name = agt
        agent_if = agent_name + "_if"
        agent_item = agent_name + "_seq_item"
        gen_if()
        gen_seq_item()
        gen_config(template_type)
        if (template_type == "act"):
            gen_driver()
            gen_seq()
            gen_sequencer()

        gen_monitor()
        gen_agent(template_type)
        gen_agent_pkg(template_type)
    template_type = "pas"
    for agt in o_agt:
        if os.path.exists(project + "/dv/agent/" + agt) != True:
            os.makedirs(project + "/dv/agent/" + agt)
        # create the agent files
        agent_name = agt
        agent_if = agent_name + "_if"
        agent_item = agent_name + "_seq_item"
        gen_if()
        gen_seq_item()
        gen_config(template_type)
        # if(template_type == "act"):
        #    gen_driver()
        #    gen_seq()
        #    gen_sequencer()
        gen_monitor()
        gen_agent(template_type)
        gen_agent_pkg(template_type)
        # gen_cov()
    gen_refm()
    gen_scb()

    # gen_tb();
    # gen_test();
    gen_top_test();
    gen_top()
    gen_top_config()
    gen_top_env()
    gen_top_pkg()

    # gen_questa_script();
    if mode == "irun":
        gen_irun_script()
        # gen_irun_script()
        # gen_vcs_script()
    else:
        gen_vcs_script()


def write_file_header(file_f):
    # f = open(file_f, "w")
    # old = f.read()
    # f.seek(0)
    file_f.write( "//=============================================================================")
    file_f.write( "// copyright");
    file_f.write( "//=============================================================================")
    file_f.write( "// Project  : " + project + "")
    file_f.write( "// File Name: $fname")
    file_f.write( "// Author   : Name   : $name")
    file_f.write( "//            Email  : $email")
    file_f.write( "//            Dept   : $dept")
    file_f.write( "// Version  : $version")
    file_f.write( "//=============================================================================")
    file_f.write( "// Description:")
    file_f.write( "//=============================================================================\n")


# end def write_file_header


def gen_if():
    global project

    dir_path = project + "/dv/agent/" + agent_name + "/"
    try:
        if_f = open(dir_path + agent_name + "_if.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open interface: " + agent_name

    write_file_header(if_f)
    if_f.write( "`ifndef " + agent_name.upper() + "_IF_SV")
    if_f.write( "`define " + agent_name.upper() + "_IF_SV\n")

    if_f.write( "interface " + agent_if + "(); \n")

    if_f.write( "  // You could add properties and assertions, for example")
    if_f.write( "  // property name ")
    if_f.write( "  // ...")
    if_f.write( "  // endproperty : name")
    if_f.write( "  // label: assert property(name) \n")

    if_f.write( "endinterface : " + agent_if + "\n")
    if_f.write( "`endif // " + agent_name.upper() + "_IF_SV")
    if_f.close()


# end gen_if


def gen_seq_item():
    global project

    dir_path = project + "/dv/agent/" + agent_name + "/"
    try:
        tr_f = open(dir_path + agent_item + ".sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open data_item: " + agent_item

    write_file_header(tr_f)
    tr_f.write( "`ifndef " + agent_item.upper() + "_SV");
    tr_f.write( "`define " + agent_item.upper() + "_SV\n");

    tr_f.write( "class " + agent_item + " extends uvm_sequence_item; ")
    tr_f.write( "  `uvm_object_utils(" + agent_item + ")\n");
    tr_f.write( "  extern function new(string name = \"" + agent_item + "\");\n");

    tr_f.write( "endclass : " + agent_item + " \n");

    tr_f.write( "function " + agent_item + "::new(string name = \"" + agent_item + "\");");
    tr_f.write( "  super.new(name);");
    tr_f.write( "endfunction : new\n");

    tr_f.write( "`endif // " + agent_item.upper() + "_SV\n")
    tr_f.close()


# end gen_data_item


def gen_config(template_type):
    global project

    dir_path = project + "/dv/agent/" + agent_name + "/"

    print
    "type = $template_type,   agent name = " + agent_name + "\n";
    try:
        cfg_f = open(dir_path + agent_name + "_agent_config.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open config: " + agent_name
    write_file_header(cfg_f)

    cfg_f.write( "`ifndef " + agent_name.upper() + "_AGENT_CONFIG_SV");
    cfg_f.write( "`define " + agent_name.upper() + "_AGENT_CONFIG_SV\n");

    cfg_f.write( "class " + agent_name + "_agent_config extends uvm_object;");

    cfg_f.write( "  `uvm_object_utils(" + agent_name + "_agent_config)\n");
    if (template_type == "pas"):
        cfg_f.write( "  rand uvm_active_passive_enum is_active = UVM_PASSIVE;\n");
    else:
        cfg_f.write( "  rand uvm_active_passive_enum is_active = UVM_ACTIVE;\n");

    cfg_f.write( "  rand bit coverage_enable = 0;");
    cfg_f.write( "  rand bit checks_enable = 0;");

    cfg_f.write( "  extern function new(string name = \"" + agent_name + "\_agent_config\");\n")

    cfg_f.write( "endclass : " + agent_name + "_agent_config \n")
    cfg_f.write( "function " + agent_name + "_agent_config::new(string name = \"" + agent_name + "\_agent_config\");")
    cfg_f.write( "  super.new(name);");
    cfg_f.write( "endfunction : new\n");

    cfg_f.write( "`endif // " + agent_name.upper() + "_AGENT_CONFIG_SV\n");
    cfg_f.close()


##end gen_config


def gen_driver():
    global project

    dir_path = project + "/dv/agent/" + agent_name + "/"
    try:
        drv_f = open(dir_path + agent_name + "_driver.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open driver: " + agent_name

    write_file_header(drv_f)

    drv_f.write( "`ifndef " + agent_name.upper() + "_DRIVER_SV")
    drv_f.write( "`define " + agent_name.upper() + "_DRIVER_SV\n")

    drv_f.write( "class " + agent_name + "_driver extends uvm_driver #(" + agent_item + ");")
    drv_f.write( "  `uvm_component_utils(" + agent_name + "_driver)\n")

    drv_f.write( "  virtual interface  " + agent_if + " vif;\n")

    drv_f.write( "  extern function new(string name, uvm_component parent);")
    drv_f.write( "  extern virtual function void build_phase (uvm_phase phase);")
    drv_f.write( "  extern virtual function void connect_phase(uvm_phase phase);")
    drv_f.write( "  extern task main_phase(uvm_phase phase);")
    drv_f.write( "  extern task do_drive(" + agent_item + " req);\n")
    drv_f.write( "endclass : " + agent_name + "_driver\n")

    drv_f.write( "function " + agent_name + "_driver::new(string name, uvm_component parent);")
    drv_f.write( "  super.new(name, parent);");
    drv_f.write( "endfunction : new\n")

    drv_f.write( "function void " + agent_name + "_driver::build_phase(uvm_phase phase);")
    drv_f.write( "  super.build_phase(phase);")
    drv_f.write( "endfunction : build_phase\n")

    drv_f.write( "function void " + agent_name + "_driver::connect_phase(uvm_phase phase);")
    drv_f.write( "  super.connect_phase(phase);\n")
    drv_f.write( "  if (!uvm_config_db #(virtual " + agent_name + '_if)::get(this, "*", "' + agent_name + "_vif\", vif))")
    drv_f.write( "    `uvm_error(\"NOVIF\", {\"virtual interface must be set for: \",get_full_name(),\".vif\"})\n")
    drv_f.write( "endfunction : connect_phase\n")

    drv_f.write( "task " + agent_name + "_driver::main_phase(uvm_phase phase);")
    # print >>drv_f, "  super.run_phase(phase);\n";
    drv_f.write( "  `uvm_info(get_type_name(), \"main_phase\", UVM_HIGH)\n")
    drv_f.write( "  forever");
    drv_f.write( "  begin");
    drv_f.write( "    seq_item_port.get_next_item(req);\n");
    drv_f.write( "      `uvm_info(get_type_name(), {\"req item\\n\",req.sprint}, UVM_HIGH)\n");
    drv_f.write( "    do_drive(req);\n");
    drv_f.write( "    //$cast(rsp, req.clone());");
    drv_f.write( "    seq_item_port.item_done();");
    drv_f.write( "    # 10ns;\n");
    drv_f.write( "  end\n");
    drv_f.write( "endtask : main_phase\n");

    drv_f.write( "task " + agent_name + "_driver::do_drive(" + agent_item + " req);\n\n");
    drv_f.write( "endtask : do_drive\n");

    drv_f.write( "`endif // " + agent_name.upper() + "_DRIVER_SV\n\n");
    drv_f.close();


# end def gen_driver


def gen_monitor():
    global project

    dir_path = project + "/dv/agent/" + agent_name + "/"
    try:
        mon_f = open(dir_path + agent_name + "_monitor.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open monitor: " + agent_name
    #
    #    write_file_header ""+agent_name+"_monitor.sv", "Monitor for "+agent_name+"";
    mon_f.write( "`ifndef " + agent_name.upper() + "_MONITOR_SV")
    mon_f.write( "`define " + agent_name.upper() + "_MONITOR_SV\n")

    mon_f.write( "class " + agent_name + "_monitor extends uvm_monitor;")
    mon_f.write( "  `uvm_component_utils(" + agent_name + "_monitor)\n")
    mon_f.write( "  virtual interface  " + agent_if + " vif;\n")
    mon_f.write( "  uvm_analysis_port #(" + agent_item + ") analysis_port;\n");

    mon_f.write( "  " + agent_item + " m_trans;\n");

    mon_f.write( "  extern function new(string name, uvm_component parent);")
    mon_f.write( "  extern virtual function void build_phase (uvm_phase phase);")
    mon_f.write( "  extern virtual function void connect_phase(uvm_phase phase);")
    mon_f.write( "  extern task main_phase(uvm_phase phase);")
    mon_f.write( "  extern task do_mon();\n")

    mon_f.write( "endclass : " + agent_name + "_monitor \n")
    mon_f.write( "function " + agent_name + "_monitor::new(string name, uvm_component parent);\n")
    mon_f.write( "  super.new(name, parent);")
    mon_f.write( "  analysis_port = new(\"analysis_port\", this);\n")
    mon_f.write( "endfunction : new\n")

    mon_f.write( "function void " + agent_name + "_monitor::build_phase(uvm_phase phase);\n")
    mon_f.write( "  super.build_phase(phase);\n")
    mon_f.write( "endfunction : build_phase\n")

    mon_f.write( "function void " + agent_name + "_monitor::connect_phase(uvm_phase phase);")
    mon_f.write( "  super.connect_phase(phase);\n")
    mon_f.write( "  if (!uvm_config_db #(virtual " + agent_name + '_if)::get(this, "*", "' + agent_name + "_vif\", vif))")
    # mon_f.write( "  if (!uvm_config_db #(virtual "+agent_name+')::get(this, "",' +agent_name+"_vif, vif))")
    mon_f.write( "    `uvm_error(\"NOVIF\",{\"virtual interface must be set for: \",get_full_name(),\".vif\"})\n")
    mon_f.write( "endfunction : connect_phase\n")

    mon_f.write( "task " + agent_name + "_monitor::main_phase(uvm_phase phase);")
    mon_f.write( "  `uvm_info(get_type_name(), \"main_phase\", UVM_HIGH)\n")
    mon_f.write( "  m_trans = " + agent_item + "::type_id::create(\"m_trans\");")
    mon_f.write( "  do_mon();\n")
    mon_f.write( "endtask : main_phase\n")

    mon_f.write( "task " + agent_name + "_monitor::do_mon();\n");
    mon_f.write( "endtask : do_mon\n");

    mon_f.write( "`endif // " + agent_name.upper() + "_MONITOR_SV\n\n");
    mon_f.close();


# end def gen_monitor


def gen_sequencer():
    global project

    dir_path = project + "/dv/agent/" + agent_name + "/"
    try:
        sqr_f = open(dir_path + agent_name + "_sequencer.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open sequencer: " + agent_name

    write_file_header(sqr_f)

    sqr_f.write( "`ifndef " + agent_name.upper() + "_SEQUENCER_SV");
    sqr_f.write( "`define " + agent_name.upper() + "_SEQUENCER_SV\n");

    sqr_f.write( "class " + agent_name + "_sequencer extends uvm_sequencer #(" + agent_item + ");");
    sqr_f.write( "  `uvm_component_utils(" + agent_name + "_sequencer)\n");

    sqr_f.write( "  extern function new(string name, uvm_component parent);\n");

    sqr_f.write( "endclass : " + agent_name + "_sequencer \n");

    sqr_f.write( "function " + agent_name + "_sequencer::new(string name, uvm_component parent);\n");
    sqr_f.write( "  super.new(name, parent);\n");
    sqr_f.write( "endfunction : new\n");

    sqr_f.write( "`endif // " + agent_name.upper() + "_SEQUENCER_SV\n\n");
    sqr_f.close();


# end def gen_sequencer


def gen_agent(template_type):
    global project

    dir_path = project + "/dv/agent/" + agent_name + "/"

    try:
        agt_f = open(dir_path + agent_name + "_agent.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open sequencer: " + agent_name
    write_file_header(agt_f)

    agt_f.write( "`ifndef " + agent_name.upper() + "_AGENT_SV")
    agt_f.write( "`define " + agent_name.upper() + "_AGENT_SV\n")

    agt_f.write( "class " + agent_name + "_agent extends uvm_agent;")
    agt_f.write( "  " + agent_name + "_agent_config       m_cfg;")
    if (template_type == "act"):
        agt_f.write( "  " + agent_name + "_sequencer          m_sequencer;")
        agt_f.write( "  " + agent_name + "_driver             m_driver;")

    agt_f.write( "  " + agent_name + "_monitor            m_monitor;\n")

    agt_f.write( "  uvm_analysis_port #(" + agent_item + ") analysis_port;\n")
    agt_f.write( "  `uvm_component_utils_begin(" + agent_name + "_agent)")
    agt_f.write( "     `uvm_field_enum(uvm_active_passive_enum, is_active, UVM_DEFAULT)")
    agt_f.write( "     `uvm_field_object(m_cfg, UVM_DEFAULT | UVM_REFERENCE)")
    agt_f.write( "  `uvm_component_utils_end\n")

    agt_f.write( "  extern function new(string name, uvm_component parent); \n")
    agt_f.write( "  extern function void build_phase(uvm_phase phase);")
    agt_f.write( "  extern function void connect_phase(uvm_phase phase);\n")

    agt_f.write( "endclass : " + agent_name + "_agent")
    agt_f.write( "\n")

    agt_f.write( "function  " + agent_name + "_agent::new(string name, uvm_component parent);")
    agt_f.write( "  super.new(name, parent);")
    agt_f.write( "  analysis_port = new(\"analysis_port\", this);")
    agt_f.write( "endfunction : new")
    agt_f.write( "\n")

    agt_f.write( "function void " + agent_name + "_agent::build_phase(uvm_phase phase);")
    agt_f.write( "  super.build_phase(phase);\n")
    agt_f.write( "  if(m_cfg == null) begin")
    agt_f.write( "    if (!uvm_config_db#(" + agent_name + "_agent_config)::get(this, \"\", \"m_cfg\", m_cfg))\n    begin")
    agt_f.write( "      `uvm_warning(\"NOCONFIG\", \"Config not set for Rx agent, using default is_active field\")")
    agt_f.write( "      m_cfg = " + agent_name + "_agent_config  ::type_id::create(\"m_cfg\", this);")
    agt_f.write( "    end")
    agt_f.write( "  end")
    agt_f.write( "  is_active = m_cfg.is_active;\n")

    agt_f.write( "  m_monitor     = " + agent_name + "_monitor    ::type_id::create(\"m_monitor\", this);")
    if (template_type == "act"):
        agt_f.write( "  if (is_active == UVM_ACTIVE)")
        agt_f.write( "  begin")
        agt_f.write( "    m_driver    = " + agent_name + "_driver     ::type_id::create(\"m_driver\", this);")
        agt_f.write( "    m_sequencer = " + agent_name + "_sequencer  ::type_id::create(\"m_sequencer\", this);")
        agt_f.write( "  end")
    agt_f.write( "endfunction : build_phase")
    agt_f.write( "\n")

    agt_f.write( "function void " + agent_name + "_agent::connect_phase(uvm_phase phase);")
    agt_f.write( "  super.connect_phase(phase);\n")
    agt_f.write( "  m_monitor.analysis_port.connect(analysis_port);")
    if (template_type == "act"):
        agt_f.write( "  if (is_active == UVM_ACTIVE)")
        agt_f.write( "  begin")
        agt_f.write( "    m_driver.seq_item_port.connect(m_sequencer.seq_item_export);")
        agt_f.write( "  end")

    agt_f.write( "endfunction : connect_phase\n")
    agt_f.write( "`endif // " + agent_name.upper() + "_AGENT_SV\n\n")
    agt_f.close()


def gen_seq():
    global project

    dir_path = project + "/dv/tests/test_seq/"
    try:
        seq_f = open(dir_path + agent_name + "_seq.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open seq: " + agent_name
    write_file_header(seq_f)

    seq_f.write( "`ifndef " + agent_name.upper() + "_SEQ_SV")
    seq_f.write( "`define " + agent_name.upper() + "_SEQ_SV\n")

    seq_f.write( "class " + agent_name + "_base_seq extends uvm_sequence #(" + agent_item + ");")
    seq_f.write( "  `uvm_object_utils(" + agent_name + "_base_seq)\n")

    seq_f.write( "  function new(string name = \"" + agent_name + "_base_seq\");")
    seq_f.write( "    super.new(name);")
    seq_f.write( "  endfunction\n")
    seq_f.write( "  virtual task pre_body();");
    seq_f.write( "    if (starting_phase != null)\n");
    seq_f.write( "    starting_phase.raise_objection(this, {\"Running sequence '\",")
    seq_f.write( "                                          get_full_name(), \"'\"});\n");
    seq_f.write( "  endtask\n");
    seq_f.write( "  virtual task post_body();");
    seq_f.write( "    if (starting_phase != null)");
    seq_f.write( "    starting_phase.drop_objection(this, {\"Completed sequence '\",");
    seq_f.write( "                                         get_full_name(), \"'\"});\n");
    seq_f.write( "  endtask\n");
    seq_f.write( "endclass : " + agent_name + "_base_seq\n");
    seq_f.write( "//-------------------------------------------------------------------------\n");

    seq_f.write( "class " + agent_name + "_seq extends " + agent_name + "_base_seq;");
    seq_f.write( "  `uvm_object_utils(" + agent_name + "_seq)\n");

    seq_f.write( "  extern function new(string name = \"" + agent_name + "\_seq\");\n");
    seq_f.write( "  extern task body();\n");
    seq_f.write( "endclass : " + agent_name + "_seq\n");

    seq_f.write( "function " + agent_name + "_seq::new(string name = \"" + agent_name + "_seq\");");
    seq_f.write( "  super.new(name);");
    seq_f.write( "endfunction : new\n");

    seq_f.write( "task " + agent_name + "_seq::body();\n");
    seq_f.write( "  `uvm_info(get_type_name(), \"Default sequence starting\", UVM_HIGH)\n\n");
    seq_f.write( "  req = " + agent_item + "::type_id::create(\"req\");\n");
    seq_f.write( "  start_item(req); \n");
    seq_f.write( "  if ( !req.randomize() )");
    seq_f.write( "    `uvm_error(get_type_name(), \"Failed to randomize transaction\")");
    seq_f.write( "  finish_item(req); \n");
    seq_f.write( "  `uvm_info(get_type_name(), \"Default sequence completed\", UVM_HIGH)\n");
    seq_f.write( "endtask : body\n");

    seq_f.write( "`endif // " + agent_name.upper() + "_SEQ_LIB_SV\n");

    seq_f.close()


# end def gen_seq


def gen_agent_pkg(template_type):
    global project

    dir_path = project + "/dv/agent/" + agent_name + "/"
    try:
        agt_pkg_f = open(dir_path + agent_name + "_pkg.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open include file: " + agent_name
    write_file_header(agt_pkg_f)

    agt_pkg_f.write( "`ifndef " + agent_name.upper() + "_PKG_SV");
    agt_pkg_f.write( "`define " + agent_name.upper() + "_PKG_SV\n");

    agt_pkg_f.write( "package " + agent_name + "_pkg;\n");
    agt_pkg_f.write( "  import uvm_pkg::*;\n");
    agt_pkg_f.write( "  `include \"uvm_macros.svh\"");
    agt_pkg_f.write( "  `include \"" + agent_item + ".sv\"");
    agt_pkg_f.write( "  `include \"" + agent_name + "_agent_config.sv\"");
    agt_pkg_f.write( "  `include \"" + agent_name + "_monitor.sv\"");

    if (template_type == "act"):
        agt_pkg_f.write( "  `include \"" + agent_name + "_driver.sv\"\n");
        agt_pkg_f.write( "  `include \"" + agent_name + "_sequencer.sv\"");
        # agt_pkg_f.write( "  `include \""+agent_name+"_coverage.sv\"\n");
        agt_pkg_f.write( "  `include \"" + agent_name + "_seq.sv\"\n");

    agt_pkg_f.write( "  `include \"" + agent_name + "_agent.sv\"\n");
    agt_pkg_f.write( "endpackage : " + agent_name + "_pkg\n");
    agt_pkg_f.write( "`endif // " + agent_name.upper() + "_PKG_SV\n");

    agt_pkg_f.close();


# end def gen_agent_pkg

def gen_top_config():
    global project
    global envname

    dir_path = project + "/dv/env/";
    try:
        env_cfg_f = open(dir_path + envname + "_config.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open config: " + envname
    write_file_header(env_cfg_f)

    env_cfg_f.write( "`ifndef " + envname.upper() + "_CONFIG_SV")
    env_cfg_f.write( "`define " + envname.upper() + "_CONFIG_SV\n")

    env_cfg_f.write( "class " + envname + "_config extends uvm_object;")
    env_cfg_f.write( "  `uvm_object_utils(" + envname + "_config)\n")
    env_cfg_f.write( "  extern function new(string name = \"" + envname + "_config\");\n")
    env_cfg_f.write( "endclass : " + envname + "_config \n")

    env_cfg_f.write( "function " + envname + "_config::new(string name = \"" + envname + "_config\");")
    env_cfg_f.write( "  super.new(name);")
    env_cfg_f.write( "endfunction : new\n");

    env_cfg_f.write( "`endif // " + envname.upper() + "_CONFIG_SV\n")
    env_cfg_f.close()


# end def gen_top_config


def gen_refm():
    global project
    global tbname

    dir_path = project + "/dv/env/";
    try:
        ref_f = open(dir_path + tbname + "_refm.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open file: $tbname"
    write_file_header(ref_f)

    ref_f.write( "`ifndef " + tbname.upper() + "_REFM_SV")
    ref_f.write( "`define " + tbname.upper() + "_REFM_SV\n")

    ref_f.write( "class " + tbname + "_refm extends uvm_component;");
    ref_f.write( "  `uvm_component_utils(" + tbname + "_refm)\n");
    ref_f.write( "//    uvm_analysis_imp#(uart_seq_item) uart_imp;\n");
    ref_f.write( "  extern function new(string name, uvm_component parent);");
    ref_f.write( "  extern task main_phase(uvm_phase phase);\n");

    ref_f.write( "endclass : " + tbname + "_refm \n");
    ref_f.write( "function " + tbname + "_refm::new(string name, uvm_component parent);\n");
    ref_f.write( "  super.new(name, parent);\n");
    ref_f.write( "endfunction : new\n");

    ref_f.write( "task " + tbname + "_refm::main_phase(uvm_phase phase);\n\n");
    ref_f.write( "endtask : main_phase\n");
    ref_f.write( "`endif // " + tbname.upper() + "_REFM_SV\n\n");
    ref_f.close();


# end def gen_refm

def gen_scb():
    global project
    global tbname

    dir_path = project + "/dv/env/";
    try:
        scb_f = open(dir_path + tbname + "_scb.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open file: $tbname"

    write_file_header(scb_f)

    scb_f.write( "`ifndef " + tbname.upper() + "_SCB_SV");
    scb_f.write( "`define " + tbname.upper() + "_SCB_SV\n");

    scb_f.write( "class " + tbname + "_scb extends uvm_component;");
    scb_f.write( "  `uvm_component_utils(" + tbname + "_scb)\n");
    scb_f.write( "  extern function new(string name, uvm_component parent);");
    scb_f.write( "  extern task main_phase(uvm_phase phase);\n");
    scb_f.write( "endclass : " + tbname + "_scb \n");

    scb_f.write( "function " + tbname + "_scb::new(string name, uvm_component parent);");
    scb_f.write( "  super.new(name, parent);");
    scb_f.write( "endfunction : new\n");

    scb_f.write( "task " + tbname + "_scb::main_phase(uvm_phase phase);\n");
    scb_f.write( "endtask : main_phase\n\n");
    scb_f.write( "`endif // " + tbname.upper() + "_SCB_SV");
    scb_f.close();


# end def gen_scb


def gen_top_env():
    global project
    global tbname

    dir_path = project + "/dv/env/"
    try:
        env_f = open(dir_path + tbname + "_env.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open file: $tbname"

    write_file_header(env_f)

    env_f.write( "`ifndef " + tbname.upper() + "_ENV_SV");
    env_f.write( "`define " + tbname.upper() + "_ENV_SV\n");

    env_f.write( "class " + tbname + "_env extends uvm_env;\n");
    env_f.write( "  `uvm_component_utils(" + tbname + "_env)\n");
    for agent in agent_list:
        env_f.write( "  " + agent + "_agent m_" + agent + "_agent; \n");
    # print >>env_f, tbname+"_refm m_"+tbname+"_refm; \n";
    # print >>env_f, tbname+"_scb m_"+tbname+"_scb; \n";

    env_f.write( "  extern function new(string name, uvm_component parent);")
    env_f.write( "  extern function void build_phase(uvm_phase phase);")
    env_f.write( "  extern function void connect_phase(uvm_phase phase);")
    env_f.write( "  extern function void end_of_elaboration_phase(uvm_phase phase);\n")

    env_f.write( "endclass : " + tbname + "_env \n");

    env_f.write( "function " + tbname + "_env::new(string name, uvm_component parent);\n")
    env_f.write( "  super.new(name, parent);\n");
    env_f.write( "endfunction : new\n");

    env_f.write( "function void " + tbname + "_env::build_phase(uvm_phase phase);")
    env_f.write( "  `uvm_info(get_type_name(), \"In build_phase\", UVM_HIGH)\n")
    env_f.write( "  //if (!uvm_config_db #(" + tbname + "_env_config)::get(this, \"\", \"m_env_config\", m_env_config)) ")
    env_f.write( "  //  `uvm_error(get_type_name(), \"Unable to get " + tbname + "_env_config\")")
    for agent in agent_list:
        env_f.write( "  m_" + agent + "_agent = " + agent + '_agent::type_id::create("m_' + agent + '_agent"), this);\n');

    # print >>env_f, "  m_refm   =  "+tbname+"_refm::type_id::create(\"m_refm\",this);"
    # print >>env_f, "  m_scb    =  "+tbname+"_scb::type_id::create(\"m_scb\",this);\n"
    env_f.write( "endfunction : build_phase\n");

    # connect phase
    env_f.write( "function void " + tbname + "_env::connect_phase(uvm_phase phase);\n");
    env_f.write( "  `uvm_info(get_type_name(), \"In connect_phase\", UVM_HIGH)\n");
    env_f.write( "endfunction : connect_phase\n");

    env_f.write( "// Could print out diagnostic information, for example\n");
    env_f.write( "function void " + tbname + "_env::end_of_elaboration_phase(uvm_phase phase);\n");
    env_f.write( "  //uvm_top.print_topology();\n");
    env_f.write( "  //`uvm_info(get_type_name(), $sformatf(\"Verbosity level is set to: %d\", get_report_verbosity_level()), UVM_MEDIUM)");
    env_f.write( "  //`uvm_info(get_type_name(), \"Print all Factory overrides\", UVM_MEDIUM)");
    env_f.write( "  //factory.print();\n");
    env_f.write( "endfunction : end_of_elaboration_phase\n");

    env_f.write( "`endif // " + tbname.upper() + "_ENV_SV\n\n");
    env_f.close();


# end def gen_top_env


def gen_top_test():
    global project
    global tbname

    dir_path = project + "/dv/tests/"
    try:
        top_test_f = open(dir_path + tbname + "_test_pkg.sv", "w")
    except IOError:
        print
        "can't open test: " + tbname + "_test_pkg.sv"

    write_file_header(top_test_f)

    top_test_f.write( "`ifndef " + tbname.upper() + "_TEST_PKG_SV")
    top_test_f.write( "`define " + tbname.upper() + "_TEST_PKG_SV\n")
    top_test_f.write( "package " + tbname + "_test_pkg;\n")
    top_test_f.write( "  `include \"uvm_macros.svh\"\n")
    top_test_f.write( "  import uvm_pkg::*;\n")

    for agent in agent_list:
        top_test_f.write( "  import " + agent + "_pkg::*;\n");

    top_test_f.write( "  import " + tbname + "_env_pkg::*;")
    top_test_f.write( "  `include \"" + tbname + "_base_test.sv\"\n")
    top_test_f.write( "endpackage : " + tbname + "_test_pkg\n")
    top_test_f.write( "`endif // " + tbname.upper() + "_TEST_PKG_SV\n")
    top_test_f.close();

    # define specific tests
    try:
        base_test_f = open(dir_path + tbname + "_base_test.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open test: " + tbname + "_base_test.sv"

    write_file_header(base_test_f)

    base_test_f.write( "`ifndef " + tbname.upper() + "_BASE_TEST_SV")
    base_test_f.write( "`define " + tbname.upper() + "_BASE_TEST_SV\n")

    base_test_f.write( "class " + tbname + "_base_test extends uvm_test;")
    base_test_f.write( "  `uvm_component_utils(" + tbname + "_base_test)\n")
    base_test_f.write( "  " + tbname + "_env           m_env;");
    base_test_f.write( "  " + tbname + "_env_config    m_env_config;")

    for agent in agent_list:
        base_test_f.write( "  " + agent + "_agent_config  m_" + agent + "_agent_config; \n");
    base_test_f.write( "  " + agent_list[0] + "_seq " + agent_list[0] + "_seq_i; \n");

    base_test_f.write( "  extern function new(string name, uvm_component parent=null);")
    base_test_f.write( "  extern function void build_phase(uvm_phase phase);")
    base_test_f.write( "  extern function void connect_phase(uvm_phase phase);")
    base_test_f.write( "  extern function void end_of_elaboration_phase(uvm_phase phase);")
    base_test_f.write( "  extern task          main_phase(uvm_phase phase);\n")
    base_test_f.write( "endclass : " + tbname + "_base_test\n");

    base_test_f.write( "function " + tbname + "_base_test::new(string name, uvm_component parent=null);")
    base_test_f.write( "  super.new(name, parent);")
    base_test_f.write( "endfunction : new\n")

    base_test_f.write( "function void " + tbname + "_base_test::build_phase(uvm_phase phase);")
    base_test_f.write( "  m_env        = " + tbname + '_env::type_id::create("m_env"), this);')
    base_test_f.write( "  m_env_config    = " + tbname + '_env_config::type_id::create("m_env_config"), this);')

    for agent in agent_list:
        base_test_f.write( "  m_" + agent + "_agent_config = " + agent + '_agent_config::type_id::create("m_' + agent + '_agent_config"), this);\n');

    base_test_f.write( "  void'(m_env_config.randomize());\n");
    base_test_f.write( "  uvm_config_db#(" + tbname + "_env_config)::set(this, \"*\", \"m_env_config\", m_env_config);\n");
    for agent in agent_list:
        base_test_f.write( "  void'(m_" + agent + "_agent_config.randomize());\n");
        base_test_f.write( "  uvm_config_db#(" + agent + '_agent_config)::set(this, "m_env.*", "m_' + agent + "_agent_config\", m_" + agent + "_agent_config);\n")

    base_test_f.write( "  " + agent_list[0] + "_seq_i = " + agent_list[0] + '_seq::type_id::create(")' + agent_list[
        0] + '_seq_i", this); \n')
    base_test_f.write( "endfunction : build_phase\n");

    base_test_f.write( "function void " + tbname + "_base_test::connect_phase(uvm_phase phase);\n");
    base_test_f.write( "endfunction : connect_phase\n");

    base_test_f.write( "function void " + tbname + "_base_test::end_of_elaboration_phase(uvm_phase phase);\n")
    base_test_f.write( "  uvm_top.print_topology();");
    base_test_f.write( "  `uvm_info(get_type_name(), $sformatf(\"Verbosity level is set to: %d\", get_report_verbosity_level()), UVM_MEDIUM)")
    base_test_f.write( "  `uvm_info(get_type_name(), \"Print all Factory overrides\", UVM_MEDIUM)")
    base_test_f.write( "  factory.print();\n")
    base_test_f.write( "endfunction : end_of_elaboration_phase\n")

    base_test_f.write( "task " + tbname + "_base_test::main_phase(uvm_phase phase);\n")
    base_test_f.write( "    super.main_phase(phase);")
    base_test_f.write( "    phase.raise_objection(this);")
    base_test_f.write( "    //seq.starting_phase = phase;")
    base_test_f.write( "    #10us;")
    base_test_f.write( "    " + agent_list[0] + "_seq_i.start(m_env.m_" + agent_list[0] + "_agent.m_sequencer);")
    base_test_f.write( "    `uvm_info(get_type_name(), \"Hello World!\", UVM_LOW)")
    base_test_f.write( "    phase.drop_objection(this);")
    base_test_f.write( "endtask : main_phase\n")

    base_test_f.write( "`endif // " + tbname.upper() + "_BASE_TEST_SV");
    base_test_f.close();


# end def gen_test_top

def gen_top_pkg():
    global project
    global tbname

    ### file list for files in sv directoru (.svh file)
    dir_path = project + "/dv/env/";
    try:
        env_pkg_f = open(dir_path + tbname + "_env_pkg.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open include file: $tbname"
    write_file_header(env_pkg_f)

    env_pkg_f.write( "package " + tbname + "_env_pkg;\n\n");
    env_pkg_f.write( "  `include \"uvm_macros.svh\"\n\n");
    env_pkg_f.write( "  import uvm_pkg::*;\n\n");
    # print >>env_pkg_f, "  import regmodel_pkg::*;\n" if $regmodel;

    for agent in agent_list:
        env_pkg_f.write( "  import " + agent + "_pkg::*;\n");
    env_pkg_f.write( "  `include \"" + tbname + "_env_config.sv\"");
    env_pkg_f.write( "  `include \"" + tbname + "_refm.sv\"");
    env_pkg_f.write( "  `include \"" + tbname + "_scb.sv\"");
    env_pkg_f.write( "  `include \"" + tbname + "_env.sv\"");
    env_pkg_f.write( "endpackage : " + tbname + "_env_pkg\n");
    env_pkg_f.close();


def gen_top():
    global project
    global tbname
    ### generate top modules
    ###Testbench
    dir_path = project + "/dv/tb/";
    try:
        file_f = open(dir_path + tbname + "_tb.sv", "w")
    except IOError:
        print
        "Exiting due to Error: can't open include file: " + tbname + "_tb.sv"

    write_file_header(file_f)
    file_f.write( "`timescale 1ns/1ns\n");
    file_f.write( "module " + tbname + "_tb;\n");
    file_f.write( "//  timeunit $timeunit;\n");
    file_f.write( "//  timeprecision $timeprecision;\n\n");
    file_f.write( "  `include \"uvm_macros.svh\"\n")
    file_f.write( "  import uvm_pkg::*;\n");

    for agent in agent_list:
        file_f.write( "  import " + agent + "_pkg::*;")
    file_f.write( "  import " + tbname + "_test_pkg::*;")
    file_f.write( "  import " + tbname + "_env_pkg::*;\n")

    for agent in agent_list:
        file_f.write( "  " + agent + "_if    m_" + agent + "_if();\n");

    file_f.write( "  ///////////////////////// \n");
    file_f.write( "  //dut u_dut(*) \n");
    file_f.write( "  ///////////////////////// \n");

    file_f.write( "  // Example clock and reset declarations\n");
    file_f.write( "  logic clock = 0;\n");
    file_f.write( "  logic reset;\n");
    file_f.write( "  // Example clock generator process\n");
    file_f.write( "  always #10 clock = ~clock;\n");

    file_f.write( "  // Example reset generator process\n");
    file_f.write( "  initial\n");
    file_f.write( "  begin\n");
    file_f.write( "    reset = 0;         // Active low reset in this example\n");
    file_f.write( "    #75 reset = 1;\n");
    file_f.write( "  end\n");
    file_f.write( "  initial\n");
    file_f.write( "  begin\n");
    for agent in (agent_list):
        file_f.write( "    uvm_config_db #(virtual " + agent + '_if)::set(null, "*", "' + agent + '_vif", m_' + agent + "_if);\n");
    file_f.write( "  end\n");

    file_f.write( "  initial\n");
    file_f.write( "  begin\n");
    file_f.write( "    run_test();\n");
    file_f.write( "  end\n");
    file_f.write( "endmodule\n");
    file_f.close();


def gen_irun_script():
    dir_path = project + "/dv/sim/";
    ius_opts = "-timescale 1ns/1ns -uvm";

    try:
        ius_f = open(dir_path + "run_irun.csh", "w")
    except IOError:
        print
        "Exiting due to Error: can't open file: run_irun.csh"
    ius_f.write( "#!/bin/sh\n\n");
    # print >>ius_f, "IUS_HOME=`ncroot`\n";
    ius_f.write( "irun " + ius_opts + " -f filelist.f -uvmhome $UVM_HOME \\")
    ius_f.write( "  +UVM_TESTNAME=" + tbname + "_base_test +UVM_VERBOSITY=UVM_FULL -l " + tbname + "_base_test.log\n");
    gen_compile_file_list()
    ius_f.close();

    ### add execute permissions for script
    os.chmod(dir_path + "run_irun.csh", 755)


def gen_vcs_script():
    dir_path = project + "/dv/sim/";
    vcs_f = open(dir_path + "Makefile", "w")

    try:
        vcs_opts = "vcs -sverilog -ntb_opts uvm -debug_pp -timescale=1ns/1ns \\";
    except IOError:
        print
        "Exiting due to Error: can't open file: Makefile"

    vcs_f.write( "#!/bin/sh\n\n")
    vcs_f.write( "RTL_PATH=../../rtl")
    vcs_f.write( "TB_PATH=../../dv")
    vcs_f.write( "VERB=UVM_MEDIUM")
    vcs_f.write( "SEED=1")
    vcs_f.write( "TEST=" + tbname + "_base_test\n")
    vcs_f.write( "all: comp run\n");

    vcs_f.write( "comp:");
    vcs_f.write( "\t") + vcs_opts
    vcs_f.write( "    -l comp.log\n")
    gen_compile_file_list()

    vcs_f.write( "run:")
    vcs_f.write( "\t./simv +UVM_TESTNAME=\${TEST} +UVM_VERBOSITY=\${VERB} +ntb_random_seed=\${SEED} -l \${TEST}.log\n")

    vcs_f.write( "dve:")
    vcs_f.write( "\tdve -vpd vcdplus.vpd&\n")

    vcs_f.write( "clean:")
    vcs_f.write( "\trm -rf csrc simv* ")

    vcs_f.close()

    ### add execute permissions for script
    os.chmod("Makefile", 755);


def gen_compile_file_list():
    global project

    dir_path = project + "/dv/sim/"
    file_f = open(dir_path + "filelist.f", "w")

    incdir = ""
    for agent in agent_list:
        incdir += "  +incdir+../agent/" + agent + "\\\n";

    incdir += "  +incdir+../tb \\\n"
    incdir += "  +incdir+../env \\\n"
    incdir += "  +incdir+../agent \\\n"
    incdir += "  +incdir+../agent/uart \\\n"
    incdir += "  +incdir+../tests \\\n"
    incdir += "  +incdir+../tests/test_seq\\\n"
    incdir += "  +incdir+../ \\\n"

    file_f.write(incdir)

    # need to compile agents before envs
    for agent in agent_list:
        file_f.write( "  ../agent/" + agent + "/" + agent + "_pkg.sv \n");
        file_f.write( "  ../agent/" + agent + "/" + agent + "_if.sv \n");

    file_f.write( "  ../agent/" + agent_name + "/" + agent_name + "_pkg.sv \\");
    file_f.write( "  ../env/" + tbname + "_env_pkg.sv \\");
    file_f.write( "  ../tests/" + tbname + "_test_pkg.sv \\");
    file_f.write( "  ../tb/" + tbname + "_tb.sv \n");
    file_f.close()


if __name__ == "__main__":
    tb_gen(sys.argv[1:])
