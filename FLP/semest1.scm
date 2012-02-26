#lang scheme

(define (simulate state expr prg lim)
        (letrec 
             (; data              
              (orientations (list 'west 'southwest 'southeast 'east 'northeast 'northwest 'west))
              
              ; general functions
              (even? ; true if argument x is even
               (lambda (x) 
                 (cond
                    ((= x 1) false)
                    ((= x 0) true)
                    ((< x 0) (even? (+ x 2)))
                    (else (even? (- x 2))) )))
              (reverse ; return reversed list l
               (lambda (l) 
                 (letrec 
                     ((rev
                       (lambda (j k) 
                         (cond
                           ((null? j) k)
                           (else (rev (cdr j) (cons (car j) k))) ))))
                   (rev l '()) )))
              (at ; i-th element of the list l
               (lambda (i l)
                 (cond
                   ((< i 0) '())
                   ((null? l) '())
                   ((= i 0) (car l))
                   (else (at (- i 1) (cdr l))) ) ))
              (apply-at ; apply fn on i-th element of the list l
               (lambda (fn i l)
                 (cond
                   ((= i 0) (cons (fn (car l)) (cdr l)))
                   ((null? l) (cons '() (apply-at fn (- i 1) (cdr l))))
                   (else (cons (car l) (apply-at fn (- i 1) (cdr l)))) )))
              (at-xy ; x-th element of y-th sublist of list l
               (lambda (x y l) (at x (at y l))))
              (apply-at-xy ; apply fn on x-th element of y-th sublist of list l
               (lambda (fn x y l) (apply-at (lambda (k) (apply-at fn x k)) y l)))
              (inc-at ; increment i-th element of the list l
               (lambda (i l) (apply-at (lambda (a) (+ a 1)) i l)))
              (dec-at ; decrement i-th element of the list l
               (lambda (i l) (apply-at (lambda (a) (- a 1)) i l)))
              (inc-at-xy ; increment x-th element of y-th sublist of list l
               (lambda (x y l) (apply-at-xy (lambda (a) (+ a 1)) x y l)))
              (dec-at-xy ; decrement x-th element of y-th sublist of list l
               (lambda (x y l) (apply-at-xy (lambda (a) (- a 1)) x y l)))
              (trunc-list ; keep first i elements of the list
               (lambda (i l)
                 (cond 
                   ((null? l) l)
                   ((= i 0) '())
                   (else (cons (car l) (trunc-list (- i 1) (cdr l)))) )))
              
              ; simulator functions
              (get-maze ; get actual maze
               (lambda (state) (at 1 state)))
              (get-coords ; coordinates of robot
               (lambda (state) (at 2 state)))
              (get-coord-x ; x-coordinate of robot
               (lambda (state) (at 0 (at 2 state)))) 
              (get-coord-y ; y-coordinate of robot
               (lambda (state) (at 1 (at 2 state))))
              (get-orientation ; get robot`s orientation
               (lambda (state) (at 3 state)))
              (set-orientation ; set robot`s orientation
               (lambda (state o) (apply-at (lambda (k) o) 3 state)))
              (push-sequence ; put somthing to action-sequence list
               ;(lambda (state a) (apply-at (lambda (o) (cons a o)) 0 state )))
               (lambda (state a) (apply-at (lambda (o) (cons (cons a (get-coords state)) o)) 0 state )))
              (inc-coord-x ; increment x-coordinate of robot
               (lambda (state) (apply-at (lambda (k) (inc-at 0 k)) 2 state)))
              (dec-coord-x ; decrement x-coordinate of robot
               (lambda (state) (apply-at (lambda (k) (dec-at 0 k)) 2 state)))
              (inc-coord-y ; increment x-coordinate of robot
               (lambda (state) (apply-at (lambda (k) (inc-at 1 k)) 2 state)))
              (dec-coord-y ; decrement x-coordinate of robot
               (lambda (state) (apply-at (lambda (k) (dec-at 1 k)) 2 state)))
              (get-failed ; return if execution subtree failed
               (lambda (state)
                 (not (null? (at 4 state))) ))
              (set-failed ; execution subtree failed
               (lambda (state reason)
                 ;(append state (list true)) ))
                 (push-sequence (append state (list true)) reason) ))
              (next-orientation ; rotate left helper function
               (lambda (o l)
                 (cond
                   ((null? l) 'fail) ; this should not happen
                   ((eq? (car l) o) (at 1 l))
                   (else (next-orientation o (cdr l))) ) ))
              (put-mark ; put mark 
               (lambda (state)
                 (apply-at (lambda (l) (inc-at-xy (get-coord-x state) (get-coord-y state) l)) 1 (push-sequence state 'put-mark))) )
              (turn-left ; rotate left 
               (lambda (state) 
                 (set-orientation (push-sequence state 'turn-left) (next-orientation (get-orientation state) orientations)) )) ; apply rotation helper
              (step ; make step without check
               (lambda (state) 
                 (push-sequence 
                  (cond 
                    ((eq? (get-orientation state) 'west) (dec-coord-x state))
                    ((eq? (get-orientation state) 'east) (inc-coord-x state))
                    ((even? (get-coord-y state))
                     (cond ((eq? (get-orientation state) 'northwest) (dec-coord-y (inc-coord-x state)))
                           ((eq? (get-orientation state) 'southwest) (inc-coord-y (inc-coord-x state)))
                           ((eq? (get-orientation state) 'northeast) (dec-coord-y state))
                           ((eq? (get-orientation state) 'southeast) (inc-coord-y state)) ) )
                    (else
                     (cond ((eq? (get-orientation state) 'northwest) (dec-coord-y state))
                           ((eq? (get-orientation state) 'southwest) (inc-coord-y state))
                           ((eq? (get-orientation state) 'northeast) (dec-coord-y (dec-coord-x state)))
                           ((eq? (get-orientation state) 'southeast) (inc-coord-y (dec-coord-x state))) ) ) )
                  'step ) ))
              (west? ; true if looking to the west
               (lambda (state)
                 (eq? (get-orientation state) 'west) ))
              (mark? ; tru if there is an mark
               (lambda (state)
                 (> (at-xy (get-coord-x state) (get-coord-y state) (get-maze state)) 0 ) ))
              (wall? ; true if there is a wall
               (lambda (state)
                 (eq? (at-xy (get-coord-x state) (get-coord-y state) (get-maze state)) 'w) ))
              (eval-if ; return branch body based on predicate
               (lambda (state expr)
                 (cond 
                   ((eq? (at 0 expr) 'wall?)
                    (cond
                      ((wall? (step state)) (cons (at 1 expr) '()))
                      (else (cons (at 2 expr) '()) ) ))
                   ((eq? (car expr) 'mark?) 
                    (cond 
                      ((mark? state) (cons (at 1 expr) '()))
                      (else (cons (at 2 expr) '()) ) ))
                   ((eq? (car expr) 'west?)
                    (cond 
                      ((west? state) (cons (at 1 expr) '()))
                      (else (cons (at 2 expr) '()) ) ))
                   (else '()) ) ))
              (get-procedure ; return procedure body
               (lambda (expr prg)
                 (cond
                   ((null? expr) '())
                   ((and (eq? (at 0 (car prg)) 'procedure) (eq? (at 1 (car prg)) expr)) (at 2 (car prg)))
                   (else (get-procedure expr (cdr prg))) )) )
              
              (do ; entry point
                  (lambda (state expr prg lim)
                    (cond 
                      ; nothing to do
                      ((null? expr)  state)
                      ; procedure recursion limit exceeded
                      ((< lim 0) (set-failed state 'recursion-lim-exceeded))
                      ; if execution subtree failed
                      ((get-failed state) (trunc-list 4 state))
                      ; another list? we need to go deeper
                      ((list? (car expr))
                       (do (do state (car expr) prg lim) (cdr expr) prg lim))
                      ; if 
                      ((eq? (car expr) 'if)
                       (do state (eval-if state (cdr expr)) prg lim))
                      ; turn left
                      ((eq? (car expr) 'turn-left)
                       (do (turn-left state) (cdr expr) prg lim))
                      ; put mark
                      ((eq? (car expr) 'put-mark)
                       (do (put-mark state) (cdr expr) prg lim))
                      ; step
                      ((eq? (car expr) 'step)
                       (let 
                           ((nextstate (step state)))
                         (cond 
                           ((wall? nextstate) (set-failed state 'stepped-to-wall))
                           (else (do nextstate (cdr expr) prg lim)) )))
                      ; handle procedure calls
                      (else 
                       (let 
                           ((prc (get-procedure (car expr) prg))) ; choose procedure body
                         (cond 
                           ((null? prc) (set-failed state 'unknown-procedure)) ; nonexisting procedure
                           (else (do (do state prc prg (- lim 1)) (cdr expr) prg lim)) )))
                      ; that`s all
                      )) )  )
          ; exec entry
          (apply-at reverse 0 (do (cons '() state) expr prg lim)) ))

(define get-maze
  '(
    (w   w   w   w   w   w)
      (w   0   w   0   w   w)
    (w   0   w   0   0   w)
      (w   0   0   0   w   w)
    (w   w   w   w   w   w)
    )
  )

(define right-hand-rule-prg
  '(
    (procedure start
               ( turn-right
                 (if wall?
                     ( turn-left
                       (if wall?
                           (turn-left
                            (if wall?
                                turn-left
                                step
                                )
                            )
                           step
                           )
                       )
                     step
                     )
                 put-mark
                 start
                 )
               )
    (procedure test ( turn-left (if wall? () step)))
    (procedure turn-right (turn-left turn-left turn-left turn-left turn-left))
    (procedure do ( (if mark? () ((if wall? (turn-left) (put-mark step))) ) do ) )
    )
  )

;(simulate (list get-maze '(1 1) 'west) 'start (list right-hand-rule-prg) 3)
(simulate (list get-maze '(1 1) 'west) '(start) right-hand-rule-prg 10)
