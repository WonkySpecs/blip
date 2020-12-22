(def first_atom
     (fn (e)
         (cond (atom e) e
               t (first_atom (first e)))))
