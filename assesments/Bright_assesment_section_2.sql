-- Horacio Morales González
-- Problem 1
-- Get how many classes are per department

select distinct data->'departamento'
	,count(distinct title) as hoy_many_classes
from classes
group by data->'departamento';

-- Problem 2
-- Get the number of months each student has been on college until today.
select name
	,current_date
	,college_enrollment_date
	,extract(YEAR FROM age(current_date ,college_enrollment_date))*12 + extract(MONTH FROM age (current_date, college_enrollment_date)) as num_months
from students;


-- Problem 3
-- Get the list of students (id and name). That is enrolled on “Matematicas II”

Select student_id
	,name
from students
WHERE 102 = ANY(enrolled_classes) 
	or 202 = ANY(enrolled_classes);

-- Problem 4
-- Get the list of all classes that have surpassed the maximum capacity of the class

with cupo_por_clase as (select A.class_id 
	,A.title
	,cast(A.data->>'max_cupo' as integer) as cupo
	,count(B.student_id) over (PARTITION BY A.class_id) as how_many
from classes A left join students B on A.class_id = any(B.enrolled_classes)
) select distinct title
	,cupo
	,how_many
from cupo_por_clase
where how_many > cupo;


-- Problem 5
-- Get the list of professors that haven’t submitted one or more grades.
select professor
from classes where class_id not in (select distinct class_id
									from grades A);

-- Problem 6
-- Explain the order in which prostgresql will run each section of the query and show what will be the final result.
explain
select
	students.name
	,classes.title
	,pass.result
from grades
	left join students using (student_id)
	left join classes using (class_id)
cross join lateral(
		select 
			case
				when grades.grade>= 7 then 'pass'
				else 'fail'
			end as result
		) as pass;

-- EXECUTION ORDER	
-- 	1) extract records from grades and the first join with students to get "name" field
--	2) extract records from classes in the second join to get the "title" field
--	3) create the lateral combination, every record in grades, with every record in subquery to get the action's name  pass or field according with the student's grade. 

--result:
--Juan	Matematicas I	pass
--Juan	Matematicas II	fail
--Juan	Fisica	fail
--Pedro	Laboratorio quimica	fail
--Pedro	Quimica Avanzada	pass
--Ana	Literatura	pass
--Ana	Laboratorio quimica	pass
--Ana	Matematicas II	fail
--Ana	Ética	fail
--Silvia	Fisica	pass
--Silvia	Ética	pass
--Silvia	Laboratorio quimica	pass
--Gerardo	Laboratorio quimica	pass