__lua__

local outer_local
if (X) goto inner_label
::outer_label::
if (X) goto exit_label

--$switch-compiler: parens8

local inner_local = outer_local
::inner_label::
if (X) goto outer_label
if (X) goto exit_label

--$switch-compiler: none

if (X) goto inner_label
local final_local = inner_local
local fine_local = outer_local
if (X) goto outer_label
::exit_label::
