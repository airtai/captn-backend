-- AddForeignKey
ALTER TABLE "UserInitialTeam" ADD CONSTRAINT "UserInitialTeam_initial_team_id_fkey" FOREIGN KEY ("initial_team_id") REFERENCES "InitialTeam"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
