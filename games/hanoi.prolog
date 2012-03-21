% Base case: move just one disk from From to To.  The intermediate tower Via
% doesn't even need to be used.
move(1, From, To, Via, Kin, Kout) :-
    writef('%w, move from %w to %w', [Kin, From, To]),
    nl,
    Kout is Kin + 1.

% To move N disks from From to To, via Via, just N-1 to Via (via To), then move a single
% disk to From, then move N-1 from Via to To (via From).
move(N, From, To, Via, Kin, Kout) :-
    Nm1 is N - 1,
    move(Nm1, From, Via, To, Kin, Kout1),
    move(1, From, To, Via, Kout1, Kout2),
    move(Nm1, Via, To, From, Kout2, Kout).


% Move N disks from From to To via Via, counting the number of moves.
move(N, From, To, Via) :- move(N, From, To, Via, 1, _).
