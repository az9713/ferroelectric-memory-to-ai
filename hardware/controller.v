// Synthesizable control only. Does not implement a ferroelectric transistor.
module controller #(parameter READ_CYCLES=2, WRITE_CYCLES=4)(
 input clk, reset, req_valid, req_write,
 input [3:0] req_addr, input [7:0] req_wdata,
 output req_ready, output reg rsp_valid, rsp_error,
 output reg [7:0] rsp_rdata,
 output mem_commit, mem_write, output [3:0] mem_addr,
 output [7:0] mem_wdata, input [7:0] mem_rdata, input mem_fault
);
 reg busy, write_latched;
 reg [3:0] addr_latched;
 reg [7:0] data_latched;
 reg [7:0] remaining;
 assign req_ready = !busy && !reset;
 assign mem_commit = busy && remaining == 1 && !reset;
 assign mem_write = write_latched;
 assign mem_addr = addr_latched;
 assign mem_wdata = data_latched;
 always @(posedge clk) begin
  if (reset) begin
   busy<=0;remaining<=0;rsp_valid<=0;rsp_error<=0;rsp_rdata<=0;
   write_latched<=0;addr_latched<=0;data_latched<=0;
  end else begin
   rsp_valid<=0;
   if (req_valid && req_ready) begin
    busy<=1;write_latched<=req_write;addr_latched<=req_addr;
    data_latched<=req_wdata;
    remaining<=req_write ? WRITE_CYCLES : READ_CYCLES;
   end else if (busy) begin
    if (remaining == 1) begin
     busy<=0;remaining<=0;rsp_valid<=1;rsp_error<=mem_fault;
     rsp_rdata<=mem_fault ? 8'h00 : mem_rdata;
    end else remaining<=remaining-1;
   end
  end
 end
endmodule
