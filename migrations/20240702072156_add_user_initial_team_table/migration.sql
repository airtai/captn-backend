-- CreateTable
CREATE TABLE "UserInitialTeam" (
    "id" SERIAL NOT NULL,
    "user_id" INTEGER NOT NULL,
    "initial_team_id" INTEGER NOT NULL,

    CONSTRAINT "UserInitialTeam_pkey" PRIMARY KEY ("id")
);
