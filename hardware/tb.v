`timescale 1ns/1ps
module tb;
 reg clk=0,reset=1,req_valid=0,req_write=0,fault=0;
 reg [3:0] req_addr=0;reg [7:0] req_wdata=0;
 wire ready,rsp_valid,rsp_error,commit,mem_write;
 wire [7:0] rsp_rdata,mem_wdata,mem_rdata;wire [3:0] mem_addr;
 integer count=0;
 always #5 clk=~clk;
 controller dut(clk,reset,req_valid,req_write,req_addr,req_wdata,ready,
  rsp_valid,rsp_error,rsp_rdata,commit,mem_write,mem_addr,mem_wdata,mem_rdata,fault);
 memory_behavior memory(clk,commit,mem_write,fault,mem_addr,mem_wdata,mem_rdata);
 task transact;
  input wr;input [3:0] addr;input [7:0] data;input bad;
  input [7:0] expected;
  integer cycles;
  begin
   @(negedge clk);if(!ready)$fatal(1,"not ready at request");
   req_valid=1;req_write=wr;req_addr=addr;req_wdata=data;fault=bad;
   @(posedge clk);#1;
   if(ready)$fatal(1,"must deassert ready after acceptance");
   @(negedge clk);req_valid=0;cycles=0;
   while(!rsp_valid)begin @(posedge clk);#1;cycles=cycles+1;end
   if(cycles!=(wr?4:2))$fatal(1,"wrong response latency: %0d",cycles);
   if(rsp_error!==bad)$fatal(1,"error propagation failed");
   if(!wr && rsp_rdata!==expected)$fatal(1,"read mismatch");
   if(!ready)$fatal(1,"did not return ready");
   count=count+1;fault=0;
  end
 endtask
 initial begin
  $dumpfile("controller.vcd");$dumpvars(0,tb);
  repeat(2)@(negedge clk);reset=0;
  transact(0,0,0,0,0);
  transact(1,0,8'ha5,0,0);transact(0,0,0,0,8'ha5);
  transact(1,15,8'h3c,0,0);transact(0,15,0,0,8'h3c);
  transact(1,15,8'hff,1,0);transact(0,15,0,0,8'h3c);
  transact(0,15,0,1,0);
  // A pulse while busy is not accepted; accepted command pins are latched.
  @(negedge clk);req_valid=1;req_write=1;req_addr=2;req_wdata=8'h55;
  @(negedge clk);req_addr=3;req_wdata=8'haa;
  @(negedge clk);req_valid=0;
  wait(rsp_valid);@(negedge clk);
  transact(0,2,0,0,8'h55);transact(0,3,0,0,0);
  // Reset aborts an in-flight write; committed nonvolatile state survives controller reset.
  @(negedge clk);req_valid=1;req_write=1;req_addr=0;req_wdata=8'h77;
  @(negedge clk);req_valid=0;reset=1;
  @(negedge clk);reset=0;
  transact(0,0,0,0,8'ha5);
  $display("PASS: %0d checked transactions; latency, endpoints, fault, busy, reset-abort, persistence",count);
  $finish;
 end
 initial begin #5000;$fatal(1,"test timeout");end
endmodule
