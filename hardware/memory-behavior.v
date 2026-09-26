// Simulation-only persistent memory abstraction. No analog physics or synthesis claim.
module memory_behavior(input clk, commit, write, fault,
 input [3:0] addr, input [7:0] wdata, output [7:0] rdata);
 reg [7:0] words [0:15];
 integer i;
 initial for(i=0;i<16;i=i+1) words[i]=0;
 assign rdata=words[addr];
 always @(posedge clk) if(commit && write && !fault) words[addr]<=wdata;
endmodule
