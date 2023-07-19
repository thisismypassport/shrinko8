__lua__
-- (the output might look like a problem, but it isn't - while assign order gets reversed, this doesn't affect which local ends up ahead in scope)
do local a=3;local b=4; printh(b)end
do local a=3;local a=4; printh(b)end


printh("over...")
