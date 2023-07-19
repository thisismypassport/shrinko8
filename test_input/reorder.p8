__lua__
do local a;local b,c=1,2;local d=4 assert(a==nil);printh(b..c..d) end

-- (the output might look like a problem, but it isn't - while assign order gets reversed, this doesn't affect which local ends up ahead in scope)
do local a=3;local b=4; printh(b)end
do local a=3;local a=4; printh(a)end

do local a;local b=3;printh(b) end
do local a;local a=3;printh(a) end


printh("over...")
